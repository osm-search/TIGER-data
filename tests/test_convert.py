import pytest

from lib.convert import compile_nodelist, compile_waylist, addressways

parsed_gisdata = [
    (
        [(1.1, 2.1), (1.2, 2.2)],
        {'tiger:way_id': 98, 'name': 'Main Rd'}
    ),
    (
        [(1.2, 2.1), (1.2, 2.2)],
        {'tiger:way_id': 99, 'name': 'Tree Rd'}
    ),
    (
        [(1.2, 2.2), (1.2, 2.3)],
        {'tiger:way_id': 99, 'name': 'Tree Rd'}
    )
]

def test_compile_nodelist():
    nodelist = compile_nodelist(parsed_gisdata)
    assert nodelist == (
        5,
        {
            (1.1, 2.1): (1, (2.1, 1.1)),
            (1.2, 2.2): (2, (2.2, 1.2)),
            (1.2, 2.1): (3, (2.1, 1.2)),
            (1.2, 2.3): (4, (2.3, 1.2))
        }
    )

def test_compile_waylist():
    waylist = compile_waylist(parsed_gisdata)
    assert waylist == {
        (('tiger:way_id', 98), ('name', 'Main Rd')): [
            [(1.1, 2.1), (1.2, 2.2)]
        ],
        (('tiger:way_id', 99), ('name', 'Tree Rd')): [
            [(1.2, 2.1), (1.2, 2.2), (1.2, 2.3)]
        ]
    }

def test_addressways():
    for geom, tags in parsed_gisdata:
        tags["tiger:lfromadd"] = 100
        tags["tiger:ltoadd"] = 200
        tags["tiger:rfromadd"] = 101
        tags["tiger:rtoadd"] = 201
        tags["tiger:zip_left"] = '55555'
        tags["tiger:zip_right"] = '55556'

    i, nodelist = compile_nodelist(parsed_gisdata)
    waylist = compile_waylist(parsed_gisdata)
    out = addressways(waylist, nodelist, i)
    assert out == [
        {
            'from': 101,
            'to': 201,
            'interpolation': 'odd',
            'postcode': '55556',
            'street': 'Main Rd',
            'city': '',
            'state': '',
            'geometry': 'LINESTRING(1.100145 2.100029,1.199971 2.199855)'
        },
        {
            'to': 200,
            'from': 100,
            'interpolation': 'even',
            'postcode': '55555',
            'street': 'Main Rd',
            'city': '',
            'state': '',
            'geometry': 'LINESTRING(1.100029 2.100145,1.199855 2.199971)'
        },
        {
            'from': 101,
            'to': 201,
            'interpolation': 'odd',
            'postcode': '55556',
            'street': 'Tree Rd',
            'city': '',
            'state': '',
            'geometry': 'LINESTRING(1.200082 2.100123,1.200082 2.200000,1.200082 2.299877)'
        },
        {
            'from': 100,
            'to': 200,
            'interpolation': 'even',
            'postcode': '55555',
            'street': 'Tree Rd',
            'city': '',
            'state': '',
            'geometry': 'LINESTRING(1.199918 2.100123,1.199918 2.200000,1.199918 2.299877)'
        }
    ]
