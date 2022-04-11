#!/usr/bin/env python3

"""
Input from STDIN is expected to be a CSV file with columns 'postcode' and
'geometry'

from;to;interpolation;street;city;state;postcode;geometry
98;88;all;Sherman Rd;Putnam;NY;10541;LINESTRING(-73.790533 41.390289,-73.790590 41.390301,...

For each postcode a center point gets calculated.

Output to STDOUT is one line per postcode

postcode,lat,lon
00535;43.089300;-72.613680
00586;18.343681;-67.028427
00601;18.181632;-66.757545
"""
from collections import defaultdict
from statistics import mean, median
from math import sqrt
import sys
import csv
import re
import logging

LOG = logging.getLogger()

postcode_summary = defaultdict(list)

reader = csv.DictReader(sys.stdin, delimiter=';')

def dist(p1, p2):
    return sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)

LOG.warning("Reading Postcodes")

cnt = 0
for row in reader:

    postcode = row['postcode']

    # In rare cases the postcode might be empty
    if not re.match(r'^\d\d\d\d\d$', postcode):
        continue

    # If you 'cat *.csv' then you might end up with multiple CSV header lines.
    # Skip those
    if row['geometry'] == 'geometry':
        continue

    result = re.match(r'LINESTRING\((.+)\)$', row['geometry'])

    # Fail if geometry can't be parsed. Shouldn't happen because it's one of
    # our scripts that created them.
    assert result

    points = result[1].split(',')
    postcode_summary[postcode].append([float(p) for p in points[int(len(points)/2)].split(' ')])

    cnt += 1

    if cnt % 1000000 == 0:
        LOG.warning("Processed %s lines.", cnt)

LOG.warning("%s lines read.", cnt)

writer = csv.DictWriter(sys.stdout, delimiter=';', fieldnames=['postcode', 'lat', 'lon'])
writer.writeheader()

maxdists = [0.1, 0.3, 0.5, 0.9]

for postcode in sorted(postcode_summary):
    points = postcode_summary[postcode]

    centroid = [median(p) for p in zip(*points)]

    for mxd in maxdists:
        filtered = [p for p in points if dist(centroid, p) < mxd]

        if len(filtered) < 0.7 * len(points):
            continue

        if len(filtered) < len(points):
            LOG.warning("%s: Found %d outliers in %d points.", postcode, - len(filtered) + len(points), len(points))
            points = filtered

        centroid = [mean(p) for p in zip(*points)]

        writer.writerow({
            'postcode': postcode,
            'lat': round(centroid[1], 6),
            'lon': round(centroid[0], 6)
        })
        break
    else:
        LOG.warning("%s: Dropped.", postcode)
