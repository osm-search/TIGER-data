import math

"""
Rounds all numbers in a list of coordinates
"""
def round_point( point, accuracy=8 ):
    return tuple( [ round(x,accuracy) for x in point ] )

"""
Returns true if two segments are connected at their beginnings or ends
"""
def adjacent( left, right ):
    left_left = round_point(left[0])
    left_right = round_point(left[-1])
    right_left = round_point(right[0])
    right_right = round_point(right[-1])

    return ( left_left == right_left or
             left_left == right_right or
             left_right == right_left or
             left_right == right_right )

"""
Returns the combination of two segments. Might reverse one or the other
to match the adjacent point of both.
"""
def glom( left, right ):
    left = list( left )
    right = list( right )

    left_left = round_point(left[0])
    left_right = round_point(left[-1])
    right_left = round_point(right[0])
    right_right = round_point(right[-1])

    if left_left == right_left:
        left.reverse()
        return left[0:-1] + right

    if left_left == right_right:
        return right[0:-1] + left

    if left_right == right_left:
        return left[0:-1] + right

    if left_right == right_right:
        right.reverse()
        return left[0:-1] + right

    raise 'segments are not adjacent'

"""
Takes a list of segments, looks at the last and tries to find an adjacent
segment in the remaining. If found combines them.
Returns a list of (now combined) segments and a list of still uncombined
segments.
"""
def glom_once( segments ):
    if len(segments)==0:
        return segments

    unsorted = list( segments )
    x = unsorted.pop(0)

    while len( unsorted ) > 0:
        n = len( unsorted )

        for i in range(0, n):
            y = unsorted[i]
            if adjacent( x, y ):
                y = unsorted.pop(i)
                x = glom( x, y )
                break

        # Sorted and unsorted lists have no adjacent segments
        if len( unsorted ) == n:
            break

    return x, unsorted

"""
Takes a list of segments and combines as many as possible together. Returns
a list of (now combined) segments.
"""
def glom_all( segments ):
    unsorted = segments
    chunks = []

    while unsorted != []:
        chunk, unsorted = glom_once( unsorted )
        chunks.append( chunk )

    return chunks


def length(segment, nodelist):
    '''Returns the length (in feet) of a segment'''
    first = True
    distance = 0
    lat_feet = 364613  #The approximate number of feet in one degree of latitude
    for point in segment:
        _pointid, (lat, lon) = nodelist[ round_point( point ) ]
        if first:
            first = False
        else:
            #The approximate number of feet in one degree of longitute
            lrad = math.radians(lat)
            lon_feet = 365527.822 * math.cos(lrad) - 306.75853 * math.cos(3 * lrad) + 0.3937 * math.cos(5 * lrad)
            distance += math.sqrt(((lat - previous[0])*lat_feet)**2 + ((lon - previous[1])*lon_feet)**2)
        previous = (lat, lon)
    return distance


def check_if_integers(numbers):
    for number in numbers:
        if not number:
            return False
        try: int(number)
        except:
            print("Non integer address: %s" % number)
            return False

    return True

def interpolation_type(this_from, this_to, other_from, other_to):
    if not check_if_integers([this_from, this_to]):
        return

    if check_if_integers([other_from, other_to]):
        if (int(this_from) % 2) == 0 and (int(this_to) % 2) == 0:
            if (int(other_from) % 2) == 1 and (int(other_to) % 2) == 1:
                return "even"

        elif (int(this_from) % 2) == 1 and (int(this_to) % 2) == 1:
            if (int(other_from) % 2) == 0 and (int(other_to) % 2) == 0:
                return "odd"

    return "all"

def create_wkt_linestring(segment):
    coord_pairs = []
    for _i, point in segment:
        coord_pairs.append( "%f %f" % (point[1], point[0]) )
    return 'LINESTRING(' + ','.join(coord_pairs) + ')'
