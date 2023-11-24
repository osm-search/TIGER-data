#!/usr/bin/env python3

import sys
from csv import DictReader
import math

# https://janakiev.com/blog/gps-points-distance-python/
# returns distance in meters
def haversine(coord1, coord2):
   R = 6372800  # Earth radius in meters
   lat1, lon1 = coord1
   lat2, lon2 = coord2

   phi1, phi2 = math.radians(lat1), math.radians(lat2)
   dphi       = math.radians(lat2 - lat1)
   dlambda    = math.radians(lon2 - lon1)

   a = math.sin(dphi/2)**2 + \
       math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2

   return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))

######################################################################
## Open and read files
##

if len(sys.argv) != 3:
    sys.exit('Expected two filenames')

filename_old = sys.argv[1]
filename_new = sys.argv[2]

postcodes_old = {}
postcodes_new = {}

with open(filename_old) as file:
    for row in DictReader(file):
        postcodes_old[row['postcode']] = {'lat': float(row['lat']), 'lon': float(row['lon'])}

with open(filename_new) as file:
    for row in DictReader(file):
        postcodes_new[row['postcode']] = {'lat': float(row['lat']), 'lon': float(row['lon'])}

print('Read %d postcodes from old file %s' % (len(postcodes_old), filename_old))
print('Read %d postcodes from new file %s' % (len(postcodes_new), filename_new))


######################################################################
## Compare files
##

num_added = 0
num_moved = 0
num_moved_100 = 0
num_moved_1000 = 0
num_moved_10000 = 0
distance_differences = 0

for postcode in postcodes_new:
    if postcode in postcodes_old:
        if (postcodes_new[postcode]['lat'] != postcodes_old[postcode]['lat']) or (postcodes_new[postcode]['lon'] != postcodes_old[postcode]['lon']):
            num_moved += 1
            distance = haversine(
                (postcodes_old[postcode]['lat'], postcodes_old[postcode]['lon']),
                (postcodes_new[postcode]['lat'], postcodes_new[postcode]['lon'])
            )
            distance_differences += distance
            if distance > 100:
                num_moved_100 += 1
            if distance > 1000:
                num_moved_1000 += 1
            if distance > 10000:
                num_moved_10000 += 1
    else:
        num_added += 1

num_deleted = 0
for postcode in postcodes_old:
    if postcode not in postcodes_new:
        num_deleted += 1



######################################################################
## Output
##

print('Added: %d (%.3f%%)' % (
    num_added,
    num_added / len(postcodes_new) * 100)
)
print('Deleted: %d (%.3f%%)' % (
    num_deleted,
    num_deleted / len(postcodes_new) * 100)
)
print('Position moved: %d (%.3f%%)' % (
    num_moved,
    num_moved / len(postcodes_new) * 100)
)
print('Position moved more than 100 meters: %d (%.3f%%)' % (
    num_moved_100,
    num_moved_100 / len(postcodes_new) * 100)
)
print('Position moved more than 1000 meters: %d (%.3f%%)' % (
    num_moved_1000,
    num_moved_1000 / len(postcodes_new) * 100)
)
print('Position moved more than 10000 meters: %d (%.3f%%)' % (
    num_moved_10000,
    num_moved_10000 / len(postcodes_new) * 100)
)
print('Average distance difference of all updates: %0.2f meters' % (
    distance_differences / num_moved)
)
