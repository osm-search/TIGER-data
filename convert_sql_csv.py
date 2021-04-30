#! /usr/bin/env python3
"""
Convert a Tiger SQL import file into CSV format.

This script is lazy and lets Postgresql do the parsing of the input files.
So essentially it loads the SQL and queries it again to get the contents of
the fields used in the parameters of the tiger_line_import() function.
That is terribly slow but circumvents all quoting quoting issues.

Lines that cannot be parsed by PostgreSQL are automatically dropped.
"""
import csv
import re
import io
import sys
import tarfile
from pathlib import Path

import psycopg2

FIELDNAMES = ['from', 'to', 'interpolation', 'street', 'city',
              'state', 'postcode', 'geometry']

def convert(sqllines):
    out = io.StringIO()
    writer = csv.DictWriter(out, FIELDNAMES, delimiter=';')
    writer.writeheader()
    conn = psycopg2.connect(dbname='nominatim')
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("""DROP FUNCTION tiger_line_import;
                       CREATE OR REPLACE FUNCTION tiger_line_import(linegeo GEOMETRY,
                                                         startnumber INTEGER,
                                                         endnumber INTEGER,
                                                         interpolationtype TEXT,
                                                         street TEXT,
                                                         isin TEXT,
                                                         postcode TEXT)
                       RETURNS TABLE (start INT, endnum INT, interpol TEXT,
                                      street TEXT, isin TEXT, postcode TEXT, geom TEXT) AS $$
                         SELECT startnumber, endnumber, interpolationtype,
                                street, isin, postcode, ST_AsTEXT(linegeo)
                       $$ LANGUAGE SQL""")

        for line in sqllines:
            line = line.decode('utf-8')
            try:
                line = line.replace('SELECT ', 'SELECT * FROM ')
                cur.execute(line)
                row = cur.fetchone()
                m = re.fullmatch(r'(.*), *([A-Z][A-Z])', row[4])
                if m:
                    writer.writerow({'from': row[0], 'to' : row[1],
                                     'interpolation' : row[2],
                                     'street' : row[3], 'city' : m.group(1),
                                     'state' : m.group(2),
                                     'postcode' : row[5], 'geometry' : row[6]})
            except psycopg2.DataError:
                # ignore invalid input
                pass
    conn.close()
    return out.getvalue()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: {} input.tar.gz output.tar.gz".format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    intar = tarfile.open(sys.argv[1])
    outtar = tarfile.open(sys.argv[2], mode='w:gz')

    for fname in intar.getmembers():
        if not fname.name.endswith('.sql'):
            print("WARNING: ignored", fname.name)
            continue

        outname = fname.name.replace('.sql', '.csv')
        print("Converting", fname.name, "to", outname)
        indata = intar.extractfile(fname)
        outdata = convert(indata).encode('utf-8')

        info = tarfile.TarInfo(name=outname)
        info.size = len(outdata)
        outtar.addfile(tarinfo=info, fileobj=io.BytesIO(outdata))

    intar.close()
    outtar.close()
