"""
Deal with coordinate system transformations/projections
"""

from osgeo import osr

osr.DontUseExceptions()

# Same as the contents of the *_edges.prj files
PROJCS_WKT = \
"""GEOGCS["GCS_North_American_1983",
        DATUM["D_North_American_1983",
        SPHEROID["GRS_1980",6378137,298.257222101]],
        PRIMEM["Greenwich",0],
        UNIT["Degree",0.017453292519943295]]"""

from_proj = osr.SpatialReference()
from_proj.ImportFromWkt(PROJCS_WKT)

# output to WGS84
to_proj = osr.SpatialReference()
to_proj.SetWellKnownGeogCS("EPSG:4326")

transformer = osr.CoordinateTransformation(from_proj, to_proj)

def unproject(point):
    """Covert point to WGS84"""
    projected = transformer.TransformPoint(point[0], point[1])
    return (round(projected[0], 6), round(projected[1], 6))
