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

import sys
import csv
import re

postcode_summary = {}

reader = csv.DictReader(sys.stdin, delimiter=';')

for row in reader:

    postcode = row['postcode']

    # In rare cases the postcode might be empty
    if not re.match(r'^\d\d\d\d\d$', postcode):
        continue

    if postcode not in postcode_summary:
        postcode_summary[postcode] = {
            'coord_count': 0,
            'lat_sum': 0,
            'lon_sum': 0
        }


    # If you 'cat *.csv' then you might end up with multiple CSV header lines.
    # Skip those
    if row['geometry'] == 'geometry':
        continue

    result = re.match(r'LINESTRING\((.+)\)$', row['geometry'])

    # Fail if geometry can't be parsed. Shouldn't happen because it's one of
    # our scripts that created them.
    assert result

    for coord_pair in result[1].split(','):
        [lon, lat] = coord_pair.split(' ')

        postcode_summary[postcode]['coord_count'] += 1
        postcode_summary[postcode]['lat_sum'] += float(lat)
        postcode_summary[postcode]['lon_sum'] += float(lon)

writer = csv.DictWriter(sys.stdout, delimiter=';', fieldnames=['postcode', 'lat', 'lon'])
writer.writeheader()

for postcode in sorted(postcode_summary):
    summary = postcode_summary[postcode]
    writer.writerow({
        'postcode': postcode,
        'lat': round(summary['lat_sum'] / summary['coord_count'], 6),
        'lon': round(summary['lon_sum'] / summary['coord_count'], 6)
    })
