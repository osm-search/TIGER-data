from lib.validate import validate_one_line, length_of_wkt_line_in_meters

def test_validate_one_line():
    line = {
        'from': '53', 
        'to': '99', 
        'interpolation': 'odd', 
        'street': 'Pope Rd', 
        'city': 'Middlesex', 
        'state': 'MA', 
        'postcode': '01720', 
        'geometry': 'LINESTRING(-71.407890 42.480238,-71.407870 42.480264,-71.407563 42.480689,-71.407061 42.481394,-71.406843 42.481731,-71.406309 42.482496,-71.406032 42.482864,-71.405533 42.483570,-71.405220 42.483994,-71.404987 42.484331,-71.404723 42.484835,-71.404551 42.485166,-71.404495 42.485385)'
    }
    assert(validate_one_line(line)) == True

    line['from'] = '-1'
    assert(validate_one_line(line)) == False
    line['from'] = '53'

    line['geometry'] = "LINESTRING(-64.937000 18.344883,-64.937000 18.344883)"
    assert(validate_one_line(line)) == False
    


def test_length_of_wkt_line_in_meters():
    wkt_line = "LINESTRING(-64.937000 18.344883,-64.937000 18.344883)"
    assert(length_of_wkt_line_in_meters(wkt_line)) == 0.0

    wkt_line = "LINESTRING(-71.196131 42.409367,-71.196170 42.409260)"
    assert(round(length_of_wkt_line_in_meters(wkt_line))) == 11

    wkt_line = "LINESTRING(-64.937000 18.344883,-64.936982 18.344751,-64.936960 18.344663,-64.936949 18.344617)"
    assert(round(length_of_wkt_line_in_meters(wkt_line))) == 29
