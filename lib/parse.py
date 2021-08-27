"""
Parse ESRI Shapefile and extract geometries and tags (key-value pairs)
"""

import os.path
import json
import re

try:
    from osgeo import ogr
except ImportError:
    import ogr

# https://www.census.gov/geo/reference/codes/cou.html
# tiger_county_fips.json was generated from the following:
# wget https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt
# cat national_county.txt | \
# perl -F, -naE'($F[0] ne 'AS') && $F[3] =~ s/ ((city|City|County|District|Borough|City and Borough|
# Municipio|Municipality|Parish|Island|Census Area)(?:, |\Z))+//;
# say qq(  "$F[1]$F[2]": "$F[3], $F[0]",)'

with open(os.path.dirname(__file__) + "/../tiger_county_fips.json", encoding="utf8") as json_file:
    county_fips_data = json.load(json_file)

def parse_shp_for_geom_and_tags(filename):
    # ogr.RegisterAll()

    ogr_driver = ogr.GetDriverByName("ESRI Shapefile")
    po_ds = ogr_driver.Open(filename)

    if po_ds is None:
        raise "Open failed."

    po_layer = po_ds.GetLayer(0)

    # fieldnames = []
    # layer_definition = po_layer.GetLayerDefn()
    # for i in range(layer_definition.GetFieldCount()):
    #     fieldnames.append(layer_definition.GetFieldDefn(i).GetName())
    # sys.stderr.write(",".join(fieldnames))

    po_layer.ResetReading()

    ret = []

    po_feature = po_layer.GetNextFeature()
    while po_feature:
        tags = get_tags_from_feature(po_feature)
        geom = get_geometry_from_feature(po_feature)

        ret.append( (geom, tags) )

        po_feature = po_layer.GetNextFeature()

    return ret

def get_geometry_from_feature(po_feature):
    geom = []
    rawgeom = po_feature.GetGeometryRef()
    for i in range( rawgeom.GetPointCount() ):
        geom.append( (rawgeom.GetX(i), rawgeom.GetY(i)) )
    return geom

def get_tags_from_feature(po_feature):
    tags = {}

    tags["tiger:way_id"] = int( po_feature.GetField("TLID") )

    if po_feature.GetField("FULLNAME"):
        tags["name"] = po_feature.GetField( "FULLNAME" )

    statefp = po_feature.GetField("STATEFP")
    countyfp = po_feature.GetField("COUNTYFP")
    if (statefp is not None) and (countyfp is not None):
        county_and_state = county_fips_data.get(statefp + '' + countyfp)
        if county_and_state: # e.g. 'Perquimans, NC'
            result = re.match('^(.+), ([A-Z][A-Z])', county_and_state)
            tags["tiger:county"] = result[1]
            tags["tiger:state"] = result[2]

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

    return tags
