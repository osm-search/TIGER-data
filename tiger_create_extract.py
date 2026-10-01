#!/usr/bin/env python3
"""
Reduce the preprocessed TIGER data set to the area a Nominatim database
actually covers.

The preprocessed TIGER archive created by this repository holds one CSV file
per US county, named after its 5-digit FIPS code (01001.csv = state 01 Alabama,
county 001). Importing all of it into a Nominatim database that only holds one
state wastes most of the work: every row is parsed, sanitized and tokenized
before SQL discovers there is no road anywhere near it, and the rows that get
discarded cost more than the rows that are kept.

This script writes the subset you need into a DIRECTORY of county CSV files,
which 'nominatim add-data --tiger-data' accepts in place of the archive:

    ./tiger_create_extract.py --states NY,NJ tiger.csv.tar.gz tiger-ny-nj/
    nominatim add-data --tiger-data tiger-ny-nj/

The source may be the packaged archive (as built by the README steps or
downloaded from the mirror) or a directory of county CSV files, such as the
output of convert.sh.
"""
import argparse
import io
import os
import shutil
import sys
import tarfile

# FIPS state codes are the leading two digits of each county file name.
#
# Transcribed verbatim from the US Census Bureau's authoritative list at
# https://www2.census.gov/geo/docs/reference/state.txt (columns STUSAB and
# STATE), linked from the ANSI/FIPS reference page at
# https://www.census.gov/library/reference/code-lists/ansi.html
#
# The gaps are real: codes are not contiguous, because several were retired
# (e.g. 03, 07, 14) and the territories start again at 60.
STATE_FIPS = {
    'AL': '01',  # Alabama
    'AK': '02',  # Alaska
    'AZ': '04',  # Arizona
    'AR': '05',  # Arkansas
    'CA': '06',  # California
    'CO': '08',  # Colorado
    'CT': '09',  # Connecticut
    'DE': '10',  # Delaware
    'DC': '11',  # District of Columbia
    'FL': '12',  # Florida
    'GA': '13',  # Georgia
    'HI': '15',  # Hawaii
    'ID': '16',  # Idaho
    'IL': '17',  # Illinois
    'IN': '18',  # Indiana
    'IA': '19',  # Iowa
    'KS': '20',  # Kansas
    'KY': '21',  # Kentucky
    'LA': '22',  # Louisiana
    'ME': '23',  # Maine
    'MD': '24',  # Maryland
    'MA': '25',  # Massachusetts
    'MI': '26',  # Michigan
    'MN': '27',  # Minnesota
    'MS': '28',  # Mississippi
    'MO': '29',  # Missouri
    'MT': '30',  # Montana
    'NE': '31',  # Nebraska
    'NV': '32',  # Nevada
    'NH': '33',  # New Hampshire
    'NJ': '34',  # New Jersey
    'NM': '35',  # New Mexico
    'NY': '36',  # New York
    'NC': '37',  # North Carolina
    'ND': '38',  # North Dakota
    'OH': '39',  # Ohio
    'OK': '40',  # Oklahoma
    'OR': '41',  # Oregon
    'PA': '42',  # Pennsylvania
    'RI': '44',  # Rhode Island
    'SC': '45',  # South Carolina
    'SD': '46',  # South Dakota
    'TN': '47',  # Tennessee
    'TX': '48',  # Texas
    'UT': '49',  # Utah
    'VT': '50',  # Vermont
    'VA': '51',  # Virginia
    'WA': '53',  # Washington
    'WV': '54',  # West Virginia
    'WI': '55',  # Wisconsin
    'WY': '56',  # Wyoming
    'AS': '60',  # American Samoa
    'GU': '66',  # Guam
    'MP': '69',  # Northern Mariana Islands
    'PR': '72',  # Puerto Rico
    'UM': '74',  # U.S. Minor Outlying Islands
    'VI': '78',  # U.S. Virgin Islands
}


def state_prefixes(states):
    """ Turn a comma-separated list of state abbreviations and/or FIPS codes
        into the set of two-digit file name prefixes to keep.
    """
    out = set()

    for state in states.upper().split(','):
        state = state.strip()
        if state in STATE_FIPS:
            out.add(STATE_FIPS[state])
        elif state.isdigit() and len(state) <= 2:
            out.add(state.zfill(2))
        elif state:
            sys.exit(f"Unknown US state '{state}'. Expected an abbreviation "
                     "like 'NY' or a FIPS code like '36'.")

    if not out:
        sys.exit("No states given.")

    return out


def line_bbox(geometry):
    """ Bounding box of a WKT LINESTRING as (minx, miny, maxx, maxy).
    """
    coords = [float(c) for p in geometry[geometry.index('(') + 1:-1].split(',')
              for c in p.split()]

    return (min(coords[0::2]), min(coords[1::2]),
            max(coords[0::2]), max(coords[1::2]))


def copy_filtered(infd, outfd, bbox):
    """ Copy CSV rows whose geometry intersects bbox, always keeping the
        header. Returns the number of data rows written, or -1 when no bbox
        was given and the file was copied verbatim.

        A return of 0 means the county has nothing inside the box; the caller
        discards the file rather than leaving a header-only CSV behind.
    """
    if bbox is None:
        shutil.copyfileobj(infd, outfd)
        return -1

    written = 0
    for i, line in enumerate(infd):
        if i == 0 or not line.strip():
            outfd.write(line)
            continue
        # The geometry is the last column and contains no ';'.
        minx, miny, maxx, maxy = line_bbox(line.rsplit(';', 1)[-1].strip())
        if not (maxx < bbox[0] or minx > bbox[2]
                or maxy < bbox[1] or miny > bbox[3]):
            outfd.write(line)
            written += 1

    return written


def parse_bbox(text):
    """ Parse a 'minx,miny,maxx,maxy' bounding box in WGS84 degrees.
    """
    try:
        coords = [float(c) for c in text.split(',')]
    except ValueError:
        sys.exit(f"Cannot parse bounding box '{text}'.")

    if len(coords) != 4:
        sys.exit("Bounding box needs exactly four numbers: "
                 "minx,miny,maxx,maxy.")

    if coords[0] > coords[2] or coords[1] > coords[3]:
        sys.exit("Bounding box must be given as minx,miny,maxx,maxy.")

    return tuple(coords)


def run(source, destination, prefixes, bbox):
    """ Write the selected county files to the destination directory.
        Returns (number of files written, number of data rows kept).
    """
    def wanted(name):
        base = os.path.basename(name)
        return base.endswith('.csv') \
            and (prefixes is None or base[:2] in prefixes)

    os.makedirs(destination, exist_ok=True)
    files = rows = 0

    if source.endswith(('.tar.gz', '.tgz')):
        with tarfile.open(source) as tar:
            for member in tar.getmembers():
                if not member.isfile() or not wanted(member.name):
                    continue
                extracted = tar.extractfile(member)
                assert extracted is not None
                outname = os.path.join(destination,
                                       os.path.basename(member.name))
                with io.TextIOWrapper(extracted, encoding='utf-8') as fdin, \
                     open(outname, 'w', encoding='utf-8') as fdout:
                    written = copy_filtered(fdin, fdout, bbox)
                if written == 0:
                    os.unlink(outname)
                    continue
                files += 1
                rows += max(written, 0)
    else:
        for name in sorted(os.listdir(source)):
            if not wanted(name):
                continue
            outname = os.path.join(destination, name)
            with open(os.path.join(source, name), encoding='utf-8') as fdin, \
                 open(outname, 'w', encoding='utf-8') as fdout:
                written = copy_filtered(fdin, fdout, bbox)
            if written == 0:
                os.unlink(outname)
                continue
            files += 1
            rows += max(written, 0)

    return files, rows


def normalize_argv(argv):
    """ Rewrite '--bbox <value>' into '--bbox=<value>'.

        Every US longitude is negative, so the natural spelling
        '--bbox -74.26,40.49,-73.70,40.92' would otherwise be rejected:
        argparse treats any token starting with '-' as an option name. This
        lets both the spaced and the '=' form work.
    """
    out = []
    i = 0

    while i < len(argv):
        if argv[i] == '--bbox' and i + 1 < len(argv):
            out.append(f'--bbox={argv[i + 1]}')
            i += 2
        else:
            out.append(argv[i])
            i += 1

    return out


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  # a single state, by abbreviation
  %(prog)s --states NY tiger.csv.tar.gz out/

  # two states by FIPS code (36 = NY, 34 = NJ)
  %(prog)s --states 36,34 tiger.csv.tar.gz out/

  # abbreviations and FIPS codes mix freely
  %(prog)s --states NY,34 tiger.csv.tar.gz out/

  # bounding box
  %(prog)s --bbox=-74.26,40.49,-73.70,40.92 \\
      tiger.csv.tar.gz out/

  # state and bounding box (faster than just bounding box)
  %(prog)s --states NY --bbox=-74.26,40.49,-73.70,40.92 \\
      tiger.csv.tar.gz out/
""")
    parser.add_argument('source', metavar='SOURCE',
                        help='TIGER .tar.gz archive, or a directory of county '
                             'CSV files')
    parser.add_argument('destination', metavar='DEST_DIR',
                        help='Output directory, created if needed')
    parser.add_argument('--states', metavar='LIST',
                        help='Comma-separated state abbreviations and/or '
                             'FIPS codes')
    parser.add_argument('--bbox', metavar='MINX,MINY,MAXX,MAXY',
                        help='Keep only rows whose geometry intersects this '
                             'box, in WGS84 degrees')

    args = parser.parse_args(normalize_argv(sys.argv[1:]))

    if not args.states and not args.bbox:
        parser.error('at least one of --states or --bbox is required')

    prefixes = state_prefixes(args.states) if args.states else None
    bbox = parse_bbox(args.bbox) if args.bbox else None

    files, rows = run(args.source, args.destination, prefixes, bbox)

    if not files:
        sys.exit(f"No matching county files found in '{args.source}'.")

    print(f"Wrote {files} county file{'' if files == 1 else 's'} "
          f"to {args.destination}"
          + (f" ({rows} rows kept)" if bbox else ""))


main()
