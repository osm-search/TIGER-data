
import math

from .project import unproject
from .helpers import round_point, glom_all, length, check_if_integers, interpolation_type, create_wkt_linestring


# Sets the distance that the address ways should be from the main way, in feet.
ADDRESS_DISTANCE = 30

# Sets the distance that the ends of the address ways should be pulled back
# from the ends of the main way, in feet
ADDRESS_PULLBACK = 45


# The approximate number of feet in one degree of latitude
LAT_FEET = 364613


def addressways(waylist, nodelist, first_way_id):
    way_id = first_way_id
    distance = float(ADDRESS_DISTANCE)
    output = []

    for tags, segments in waylist.items():
        tags = dict(tags)
        for segment in segments:
            lsegment = []
            rsegment = []
            lastpoint = []

            # Don't pull back the ends of very short ways too much
            seglength = length(segment, nodelist)
            if seglength < float(ADDRESS_PULLBACK) * 3.0:
                pullback = seglength / 3.0
            else:
                pullback = float(ADDRESS_PULLBACK)

            lfromadd = tags.get("tiger:lfromadd")
            ltoadd = tags.get("tiger:ltoadd")
            rfromadd = tags.get("tiger:rfromadd")
            rtoadd = tags.get("tiger:rtoadd")

            right = check_if_integers([rfromadd, rtoadd])
            left = check_if_integers([lfromadd, ltoadd])

            if not left and not right:
                continue

            first = True
            firstpointid, firstpoint = nodelist[ round_point( segment[0] ) ]
            finalpointid, finalpoint = nodelist[ round_point( segment[len(segment) - 1] ) ]

            for point in segment:
                pointid, (lat, lon) = nodelist[ round_point( point ) ]

                # The approximate number of feet in one degree of longitude
                lrad = math.radians(lat)
                LON_FEET = 365527.822 * math.cos(lrad) - 306.75853 * math.cos(3 * lrad) + 0.3937 * math.cos(5 * lrad)

                # Calculate the points of the offset ways
                if lastpoint:
                    # Skip points too close to start
                    if math.sqrt((lat * LAT_FEET - firstpoint[0] * LAT_FEET)**2 + (lon * LON_FEET - firstpoint[1] * LON_FEET)**2) < pullback:
                        # Preserve very short ways (but will be rendered backwards)
                        if pointid != finalpointid:
                            continue
                    # Skip points too close to end
                    if math.sqrt((lat * LAT_FEET - finalpoint[0] * LAT_FEET)**2 + (lon * LON_FEET - finalpoint[1] * LON_FEET)**2) < pullback:
                        # Preserve very short ways (but will be rendered backwards)
                        if pointid not in (firstpointid, finalpointid):
                            continue

                    X = (lon - lastpoint[1]) * LON_FEET
                    Y = (lat - lastpoint[0]) * LAT_FEET
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
                        dX =  - (Yp * (pullback / distance)) / LON_FEET #Pull back the first point
                        dY = (Xp * (pullback / distance)) / LAT_FEET
                        if left:
                            lpoint = (lastpoint[0] + (Yp / LAT_FEET) - dY, lastpoint[1] + (Xp / LON_FEET) - dX)
                            lsegment.append( (way_id, lpoint) )
                            way_id += 1
                        if right:
                            rpoint = (lastpoint[0] - (Yp / LAT_FEET) - dY, lastpoint[1] - (Xp / LON_FEET) - dX)
                            rsegment.append( (way_id, rpoint) )
                            way_id += 1

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
                            lpoint = (lastpoint[0] + (Yp + delta[0]) * r / (LAT_FEET * 2), lastpoint[1] + (Xp + delta[1]) * r / (LON_FEET * 2))
                            lsegment.append( (way_id, lpoint) )
                            way_id += 1
                        if right:
                            rpoint = (lastpoint[0] - (Yp + delta[0]) * r / (LAT_FEET * 2), lastpoint[1] - (Xp + delta[1]) * r / (LON_FEET * 2))
                            rsegment.append( (way_id, rpoint) )
                            way_id += 1

                    delta = (Yp, Xp)

                lastpoint = (lat, lon)


            # Add in the last node
            dX =  - (Yp * (pullback / distance)) / LON_FEET
            dY = (Xp * (pullback / distance)) / LAT_FEET
            if left:
                lpoint = (lastpoint[0] + (Yp + delta[0]) / (LAT_FEET * 2) + dY, lastpoint[1] + (Xp + delta[1]) / (LON_FEET * 2) + dX )
                lsegment.append( (way_id, lpoint) )
                way_id += 1
            if right:
                rpoint = (lastpoint[0] - Yp / LAT_FEET + dY, lastpoint[1] - Xp / LON_FEET + dX)
                rsegment.append( (way_id, rpoint) )
                way_id += 1

            # Generate the tags for ways and nodes
            zipr = tags.get("tiger:zip_right", '')
            zipl = tags.get("tiger:zip_left", '')
            name = tags.get("name", '')
            county = tags.get("tiger:county", '')
            state = tags.get("tiger:state", '')

            # Write the nodes of the offset ways
            if right:
                interpolationtype = interpolation_type(rfromadd, rtoadd, lfromadd, ltoadd)

                output.append({
                    'from': rfromadd,
                    'to': rtoadd,
                    'interpolation': interpolationtype,
                    'street': name,
                    'city': county,
                    'state': state,
                    'postcode': zipr,
                    'geometry': create_wkt_linestring(rsegment)
                })

            if left:
                interpolationtype = interpolation_type(lfromadd, ltoadd, rfromadd, rtoadd)

                output.append({
                    'from': lfromadd,
                    'to': ltoadd,
                    'interpolation': interpolationtype,
                    'street': name,
                    'city': county,
                    'state': state,
                    'postcode': zipl,
                    'geometry': create_wkt_linestring(lsegment)
                })

    return output

def compile_nodelist(parsed_gisdata):
    nodelist = {}

    i = 1
    for geom, _tags in parsed_gisdata:
        for point in geom:
            r_point = round_point(point)
            if r_point not in nodelist:
                nodelist[r_point] = (i, unproject(point))
                i += 1

    return (i, nodelist)



def compile_waylist(parsed_gisdata):
    waylist = {}

    # Group by tiger:way_id
    for geom, tags in parsed_gisdata:
        way_key = tags.copy()
        # {'tiger:way_id': 18403490, 'name': 'Holly St', 'tiger:county': 'Perquimans', 'tiger:state': 'NC'}
        way_key = ( way_key['tiger:way_id'], tuple( [(k,v) for k,v in way_key.items()] ) )
        # (18403490, (('tiger:way_id', 18403490), ('name', 'Holly St'), ('tiger:county', 'Perquimans'), ('tiger:state', 'NC')))

        if way_key not in waylist:
            waylist[way_key] = []

        waylist[way_key].append(geom)

    ret = {}
    for (_way_id, way_key), segments in waylist.items():
        ret[way_key] = glom_all( segments )
    return ret
