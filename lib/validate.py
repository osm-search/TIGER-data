from math import cos, radians
from osgeo import ogr, osr

METERS_PER_DEGREE_LAT = 111132

def validate_one_line(fields):
    if int(fields['from']) < 0 or int(fields['to']) < 0:
        print('Negative housenumber, skipping')
        return False

    number_range = abs(int(fields['from']) - int(fields['to']))
    step_size = 1 if fields['interpolation'] == 'all' else 2
    length = length_of_wkt_line_in_meters(fields['geometry'])
    if number_range > 0 and length < 10:
        print('Interpolation less than 10 meters, skipping')
        return False

    return True

def length_of_wkt_line_in_meters(wkt_line):
    line = ogr.CreateGeometryFromWkt(wkt_line)

    center_lat = line.Centroid().GetY()

    meters_per_degree_lon = METERS_PER_DEGREE_LAT * cos(radians(center_lat))

    length_degrees = line.Length()
    length_meters = length_degrees * (METERS_PER_DEGREE_LAT + meters_per_degree_lon) / 2

    return length_meters
