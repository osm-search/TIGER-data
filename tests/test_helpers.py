import pytest

from lib.helpers import round_point, adjacent, glom, check_if_integers, interpolation_type, create_wkt_linestring

def test_round_point():
    assert round_point([1.0, 1.0]) == (1.0, 1.0)
    assert round_point([12.345, 56.789], 1) == (12.3, 56.8)

def test_adjacent():
    line1 = [[1,1], [1,5]]
    line2 = [[2,2], [1,5]]
    line3 = [[2,2], [1,1]]
    line4 = [[5,6], [6,5]]
    assert adjacent(line1, line2) is True
    assert adjacent(line1, line3) is True
    assert adjacent(line1, line4) is False

def test_glom():
    line1 = [[1,1], [1,2], [1,3]]
    line2 = [[2,2], [2,3], [1,3]]

    # line1 + reversed line2
    assert glom(line1, line2) == [[1,1], [1,2], [1,3], [2,3], [2,2]]

def test_check_if_integers():
    assert check_if_integers([1, 2, 3])
    assert check_if_integers(['b']) is False
    assert check_if_integers([None]) is False
    assert check_if_integers(['']) is False

def test_interpolation_type():
    assert interpolation_type(100, 200, 101, 201) == "even"
    assert interpolation_type(101, 201, 100, 200) == "odd"
    assert interpolation_type(101, 202, 100, 200) == "all"

    assert interpolation_type('abc', 202, 100, 200) is None
    assert interpolation_type(100, 200, 'abc', 201) == "all"

def test_create_wkt_linestring():
    segment = [
        (1, (100, 200)),
        (2, (101, 201))
    ]
    assert(create_wkt_linestring(segment)) == 'LINESTRING(200.000000 100.000000,201.000000 101.000000)'