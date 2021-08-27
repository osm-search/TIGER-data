#!/usr/bin/python3

"""
Tiger road data to OSM conversion script
Creates Karlsruhe-style address ways beside the main way
based on the Massachusetts GIS script by christopher schmidt

BUGS:
- On very tight curves, a loop may be generated in the address way.
- It would be nice if the ends of the address ways were not pulled back from dead ends
"""

import sys
import os.path
import json
import re
import csv
import math

from lib.helpers import round_point, glom_all, length

try:
    from osgeo import ogr
    from osgeo import osr
except:
    import ogr
    import osr

# Ways that include these mtfccs should not be uploaded
# H1100 Connector
# H3010 Stream/River
# H3013 Braided Stream
# H3020 Canal, Ditch or Aqueduct
# L4130 Point-to-Point Line
# L4140 Property/Parcel Line (Including PLSS)
# P0001 Nonvisible Linear Legal/Statistical Boundary
# P0002 Perennial Shoreline
# P0003 Intermittent Shoreline
# P0004 Other non-visible bounding Edge (e.g., Census water boundary, boundary of an areal feature)
ignoremtfcc = [
    "H1100",
    "H3010",
    "H3013",
    "H3020",
    "L4130",
    "L4140",
    "P0001",
    "P0002",
    "P0003",
    "P0004"
]

# Sets the distance that the address ways should be from the main way, in feet.
ADDRESS_DISTANCE = 30

# Sets the distance that the ends of the address ways should be pulled back
# from the ends of the main way, in feet
ADDRESS_PULLBACK = 45


# https://www.census.gov/geo/reference/codes/cou.html
# tiger_county_fips.json was generated from the following:
# wget https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt
# cat national_county.txt | perl -F, -naE'($F[0] ne 'AS') && $F[3] =~ s/ ((city|City|County|District|Borough|City and Borough|Municipio|Municipality|Parish|Island|Census Area)(?:, |\Z))+//; say qq(  "$F[1]$F[2]": "$F[3], $F[0]",)'
json_fh = open(os.path.dirname(sys.argv[0]) + "/tiger_county_fips.json")
county_fips_data = json.load(json_fh)

def parse_shp_for_geom_and_tags( filename ):
    #ogr.RegisterAll()

    dr = ogr.GetDriverByName("ESRI Shapefile")
    po_ds = dr.Open( filename )

    if po_ds is None:
        raise "Open failed."

    po_layer = po_ds.GetLayer( 0 )

    fieldNameList = []
    layer_definition = po_layer.GetLayerDefn()
    for i in range(layer_definition.GetFieldCount()):
        fieldNameList.append(layer_definition.GetFieldDefn(i).GetName())
    # sys.stderr.write(",".join(fieldNameList))

    po_layer.ResetReading()

    ret = []

    po_feature = po_layer.GetNextFeature()
    while po_feature:
        tags = {}

        # WAY ID
        tags["tiger:way_id"] = int( po_feature.GetField("TLID") )

        # FEATURE IDENTIFICATION
        mtfcc = po_feature.GetField("MTFCC")
        if mtfcc is not None:

            if mtfcc == "L4010":        #Pipeline
                tags["man_made"] = "pipeline"
            if mtfcc == "L4020":        #Powerline
                tags["power"] = "line"
            if mtfcc == "L4031":        #Aerial Tramway/Ski Lift
                tags["aerialway"] = "cable_car"
            if mtfcc == "L4110":        #Fence Line
                tags["barrier"] = "fence"
            if mtfcc == "L4125":        #Cliff/Escarpment
                tags["natural"] = "cliff"
            if mtfcc == "L4165":        #Ferry Crossing
                tags["route"] = "ferry"
            if mtfcc == "R1011":        #Railroad Feature (Main, Spur, or Yard)
                tags["railway"] = "rail"
                ttyp = po_feature.GetField("TTYP")
                if ttyp is not None:
                    if ttyp == "S":
                        tags["service"] = "spur"
                    if ttyp == "Y":
                        tags["service"] = "yard"
                    tags["tiger:ttyp"] = ttyp
            if mtfcc == "R1051":        # Carline, Streetcar Track, Monorail, Other Mass Transit Rail
                tags["railway"] = "light_rail"
            if mtfcc == "R1052":        #Cog Rail Line, Incline Rail Line, Tram
                tags["railway"] = "incline"
            if mtfcc == "S1100":
                tags["highway"] = "primary"
            if mtfcc == "S1200":
                tags["highway"] = "secondary"
            if mtfcc == "S1400":
                tags["highway"] = "residential"
            if mtfcc == "S1500":
                tags["highway"] = "track"
            if mtfcc == "S1630":        #Ramp
                tags["highway"] = "motorway_link"
            if mtfcc == "S1640":        #Service Drive usually along a limited access highway
                tags["highway"] = "service"
            if mtfcc == "S1710":        #Walkway/Pedestrian Trail
                tags["highway"] = "path"
            if mtfcc == "S1720":
                tags["highway"] = "steps"
            if mtfcc == "S1730":        #Alley
                tags["highway"] = "service"
                tags["service"] = "alley"
            if mtfcc == "S1740":        #Private Road for service vehicles (logging, oil, fields, ranches, etc.)
                tags["highway"] = "service"
                tags["access"] = "private"
            if mtfcc == "S1750":        #Private Driveway
                tags["highway"] = "service"
                tags["access"] = "private"
                tags["service"] = "driveway"
            if mtfcc == "S1780":        #Parking Lot Road
                tags["highway"] = "service"
                tags["service"] = "parking_aisle"
            if mtfcc == "S1820":        #Bike Path or Trail
                tags["highway"] = "cycleway"
            if mtfcc == "S1830":        #Bridle Path
                tags["highway"] = "bridleway"
            tags["tiger:mtfcc"] = mtfcc

        # FEATURE NAME
        if po_feature.GetField("FULLNAME"):
            #capitalizes the first letter of each word
            name = po_feature.GetField( "FULLNAME" )
            tags["name"] = name

            #Attempt to guess highway grade
            if name[0:2] == "I-":
                tags["highway"] = "motorway"
            if name[0:3] == "US ":
                tags["highway"] = "primary"
            if name[0:3] == "US-":
                tags["highway"] = "primary"
            if name[0:3] == "Hwy":
                if tags["highway"] != "primary":
                    tags["highway"] = "secondary"

        statefp = po_feature.GetField("STATEFP")
        countyfp = po_feature.GetField("COUNTYFP")
        if (statefp is not None) and (countyfp is not None):
            county_name = county_fips_data.get(statefp + '' + countyfp)
            if county_name:
                tags["tiger:county"] = county_name

        # tlid = po_feature.GetField("TLID")
        # if tlid is not None:
        #     tags["tiger:tlid"] = tlid

        lfromadd = po_feature.GetField("LFROMADD")
        if lfromadd is not None:
            tags["tiger:lfromadd"] = lfromadd

        rfromadd = po_feature.GetField("RFROMADD")
        if rfromadd is not None:
            tags["tiger:rfromadd"] = rfromadd

        ltoadd = po_feature.GetField("LTOADD")
        if ltoadd is not None:
            tags["tiger:ltoadd"] = ltoadd

        rtoadd = po_feature.GetField("RTOADD")
        if rtoadd is not None:
            tags["tiger:rtoadd"] = rtoadd

        zipl = po_feature.GetField("ZIPL")
        if zipl is not None:
            tags["tiger:zip_left"] = zipl

        zipr = po_feature.GetField("ZIPR")
        if zipr is not None:
            tags["tiger:zip_right"] = zipr

        if mtfcc not in ignoremtfcc:
            # COPY DOWN THE GEOMETRY
            geom = []

            rawgeom = po_feature.GetGeometryRef()
            for i in range( rawgeom.GetPointCount() ):
                geom.append( (rawgeom.GetX(i), rawgeom.GetY(i)) )

            ret.append( (geom, tags) )
        po_feature = po_layer.GetNextFeature()

    return ret


# ====================================
# to do read .prj file for this data
# Change the PROJCS_WKT to match your datas prj file.
# ====================================
PROJCS_WKT = \
"""GEOGCS["GCS_North_American_1983",
        DATUM["D_North_American_1983",
        SPHEROID["GRS_1980",6378137,298.257222101]],
        PRIMEM["Greenwich",0],
        UNIT["Degree",0.017453292519943295]]"""

from_proj = osr.SpatialReference()
from_proj.ImportFromWkt( PROJCS_WKT )

# output to WGS84
to_proj = osr.SpatialReference()
to_proj.SetWellKnownGeogCS( "EPSG:4326" )

tr = osr.CoordinateTransformation( from_proj, to_proj )


def addressways(waylist, nodelist, first_id):
    id = first_id
    lat_feet = 364613  #The approximate number of feet in one degree of latitude
    distance = float(ADDRESS_DISTANCE)
    csv_lines = []

    for waykey, segments in waylist.items():
        waykey = dict(waykey)
        rsegments = []
        lsegments = []
        for segment in segments:
            lsegment = []
            rsegment = []
            lastpoint = None

            # Don't pull back the ends of very short ways too much
            seglength = length(segment, nodelist)
            if seglength < float(ADDRESS_PULLBACK) * 3.0:
                pullback = seglength / 3.0
            else:
                pullback = float(ADDRESS_PULLBACK)
            if "tiger:lfromadd" in waykey:
                lfromadd = waykey["tiger:lfromadd"]
            else:
                lfromadd = None
            if "tiger:ltoadd" in waykey:
                ltoadd = waykey["tiger:ltoadd"]
            else:
                ltoadd = None
            if "tiger:rfromadd" in waykey:
                rfromadd = waykey["tiger:rfromadd"]
            else:
                rfromadd = None
            if "tiger:rtoadd" in waykey:
                rtoadd = waykey["tiger:rtoadd"]
            else:
                rtoadd = None
            if rfromadd is not None and rtoadd is not None:
                right = True
            else:
                right = False
            if lfromadd is not None and ltoadd is not None:
                left = True
            else:
                left = False
            if left or right:
                first = True
                firstpointid, firstpoint = nodelist[ round_point( segment[0] ) ]

                finalpointid, finalpoint = nodelist[ round_point( segment[len(segment) - 1] ) ]
                for point in segment:
                    pointid, (lat, lon) = nodelist[ round_point( point ) ]

                    #The approximate number of feet in one degree of longitute
                    lrad = math.radians(lat)
                    lon_feet = 365527.822 * math.cos(lrad) - 306.75853 * math.cos(3 * lrad) + 0.3937 * math.cos(5 * lrad)

#Calculate the points of the offset ways
                    if lastpoint is not None:
                        #Skip points too close to start
                        if math.sqrt((lat * lat_feet - firstpoint[0] * lat_feet)**2 + (lon * lon_feet - firstpoint[1] * lon_feet)**2) < pullback:
                            #Preserve very short ways (but will be rendered backwards)
                            if pointid != finalpointid:
                                continue
                        #Skip points too close to end
                        if math.sqrt((lat * lat_feet - finalpoint[0] * lat_feet)**2 + (lon * lon_feet - finalpoint[1] * lon_feet)**2) < pullback:
                            #Preserve very short ways (but will be rendered backwards)
                            if (pointid != firstpointid) and (pointid != finalpointid):
                                continue

                        X = (lon - lastpoint[1]) * lon_feet
                        Y = (lat - lastpoint[0]) * lat_feet
                        if Y != 0:
                            theta = math.pi/2 - math.atan( X / Y)
                            Xp = math.sin(theta) * distance
                            Yp = math.cos(theta) * distance
                        else:
                            Xp = 0
                            if X > 0:
                                Yp = -distance
                            else:
                                Yp = distance

                        if Y > 0:
                            Xp = -Xp
                        else:
                            Yp = -Yp

                        if first:
                            first = False
                            dX =  - (Yp * (pullback / distance)) / lon_feet #Pull back the first point
                            dY = (Xp * (pullback / distance)) / lat_feet
                            if left:
                                lpoint = (lastpoint[0] + (Yp / lat_feet) - dY, lastpoint[1] + (Xp / lon_feet) - dX)
                                lsegment.append( (id, lpoint) )
                                id += 1
                            if right:
                                rpoint = (lastpoint[0] - (Yp / lat_feet) - dY, lastpoint[1] - (Xp / lon_feet) - dX)
                                rsegment.append( (id, rpoint) )
                                id += 1

                        else:
                            #round the curves
                            if delta[1] != 0:
                                theta = abs(math.atan(delta[0] / delta[1]))
                            else:
                                theta = math.pi / 2
                            if Xp != 0:
                                theta = theta - abs(math.atan(Yp / Xp))
                            else: theta = theta - math.pi / 2
                            r = 1 + abs(math.tan(theta/2))
                            if left:
                                lpoint = (lastpoint[0] + (Yp + delta[0]) * r / (lat_feet * 2), lastpoint[1] + (Xp + delta[1]) * r / (lon_feet * 2))
                                lsegment.append( (id, lpoint) )
                                id += 1
                            if right:
                                rpoint = (lastpoint[0] - (Yp + delta[0]) * r / (lat_feet * 2), lastpoint[1] - (Xp + delta[1]) * r / (lon_feet * 2))

                                rsegment.append( (id, rpoint) )
                                id += 1

                        delta = (Yp, Xp)

                    lastpoint = (lat, lon)


#Add in the last node
                dX =  - (Yp * (pullback / distance)) / lon_feet
                dY = (Xp * (pullback / distance)) / lat_feet
                if left:
                    lpoint = (lastpoint[0] + (Yp + delta[0]) / (lat_feet * 2) + dY, lastpoint[1] + (Xp + delta[1]) / (lon_feet * 2) + dX )
                    lsegment.append( (id, lpoint) )
                    id += 1
                if right:
                    rpoint = (lastpoint[0] - Yp / lat_feet + dY, lastpoint[1] - Xp / lon_feet + dX)
                    rsegment.append( (id, rpoint) )
                    id += 1

#Generate the tags for ways and nodes
                zipr = ''
                zipl = ''
                name = ''
                county = ''
                state = ''
                if "tiger:zip_right" in waykey:
                    zipr = waykey["tiger:zip_right"]
                if "tiger:zip_left" in waykey:
                    zipl = waykey["tiger:zip_left"]
                if "name" in waykey:
                    name = waykey["name"]
                if "tiger:county" in waykey:
                    result = re.match('^(.+), ([A-Z][A-Z])', waykey["tiger:county"]) # e.g. 'Perquimans, NC'
                    county = result[1]
                    state = result[2]

#Write the nodes of the offset ways
                if right:
                    rlinestring = []
                    for _i, point in rsegment:
                        rlinestring.append( "%f %f" % (point[1], point[0]) )
                if left:
                    llinestring = []
                    for _i, point in lsegment:
                        llinestring.append( "%f %f" % (point[1], point[0]) )
                if right:
                    rsegments.append( rsegment )
                if left:
                    lsegments.append( lsegment )
                rtofromint = right        #Do the addresses convert to integers?
                ltofromint = left        #Do the addresses convert to integers?
                if right:
                    try: rfromint = int(rfromadd)
                    except:
                        print("Non integer address: %s" % rfromadd)
                        rtofromint = False
                    try: rtoint = int(rtoadd)
                    except:
                        print("Non integer address: %s" % rtoadd)
                        rtofromint = False
                if left:
                    try: lfromint = int(lfromadd)
                    except:
                        print("Non integer address: %s" % lfromadd)
                        ltofromint = False
                    try: ltoint = int(ltoadd)
                    except:
                        print("Non integer address: %s" % ltoadd)
                        ltofromint = False
                if right:
                    id += 1

                    interpolationtype = "all"
                    if rtofromint:
                        if (rfromint % 2) == 0 and (rtoint % 2) == 0:
                            if ltofromint and (lfromint % 2) == 1 and (ltoint % 2) == 1:
                                interpolationtype = "even"
                        elif (rfromint % 2) == 1 and (rtoint % 2) == 1:
                            if ltofromint and (lfromint % 2) == 0 and (ltoint % 2) == 0:
                                interpolationtype = "odd"

                        csv_lines.append({
                            'from': int(rfromadd),
                            'to': int(rtoadd),
                            'interpolation': interpolationtype,
                            'street': name,
                            'city': county,
                            'state': state,
                            'postcode': zipr,
                            'geometry': 'LINESTRING(' + ','.join(rlinestring) + ')'
                        })
                if left:
                    id += 1

                    interpolationtype = "all"
                    if ltofromint:
                        if (lfromint % 2) == 0 and (ltoint % 2) == 0:
                            if rtofromint and (rfromint % 2) == 1 and (rtoint % 2) == 1:
                                interpolationtype = "even"
                        elif (lfromint % 2) == 1 and (ltoint % 2) == 1:
                            if rtofromint and (rfromint %2 ) == 0 and (rtoint % 2) == 0:
                                interpolationtype = "odd"

                        csv_lines.append({
                            'from': int(lfromadd),
                            'to': int(ltoadd),
                            'interpolation': interpolationtype,
                            'street': name,
                            'city': county,
                            'state': state,
                            'postcode': zipl,
                            'geometry': 'LINESTRING(' + ','.join(llinestring) + ')'
                        })

    return csv_lines

def unproject( point ):
    pt = tr.TransformPoint( point[0], point[1] )
    return (pt[0], pt[1])

def compile_nodelist( parsed_gisdata, first_id=1 ):
    nodelist = {}

    i = first_id
    for geom, _tags in parsed_gisdata:
        if len( geom )==0:
            continue

        for point in geom:
            r_point = round_point( point )
            if r_point not in nodelist:
                nodelist[ r_point ] = (i, unproject( point ))
                i += 1

    return (i, nodelist)




def compile_waylist( parsed_gisdata ):
    waylist = {}

    #Group by tiger:way_id
    for geom, tags in parsed_gisdata:
        way_key = tags.copy()
        way_key = ( way_key['tiger:way_id'], tuple( [(k,v) for k,v in way_key.items()] ) )

        if way_key not in waylist:
            waylist[way_key] = []

        waylist[way_key].append( geom )

    ret = {}
    for (_way_id, way_key), segments in waylist.items():
        ret[way_key] = glom_all( segments )
    return ret


def shape_to_csv( shp_filename, csv_filename ):

    print("parsing shpfile %s" % shp_filename)
    parsed_features = parse_shp_for_geom_and_tags( shp_filename )

    print("compiling nodelist")
    i, nodelist = compile_nodelist( parsed_features )

    print("compiling waylist")
    waylist = compile_waylist( parsed_features )

    print("preparing address ways")
    csv_lines = addressways(waylist, nodelist, i)

    print("writing %s" % csv_filename)
    fieldnames = ['from', 'to', 'interpolation', 'street', 'city', 'state', 'postcode', 'geometry']
    with open(csv_filename, 'w') as f:
        csv_writer = csv.DictWriter(f, delimiter=';', fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(csv_lines)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("%s input.shp output.csv" % sys.argv[0])
        sys.exit()
    shp_filename = sys.argv[1]
    csv_filename = sys.argv[2]
    shape_to_csv(shp_filename, csv_filename)
