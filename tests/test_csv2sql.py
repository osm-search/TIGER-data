from csv import DictReader
from lib.csv2sql import csv_row_to_sql

def test_csv_row_to_sql_insert_statement():
    expected_sql = """\
SELECT tiger_line_import(ST_GeomFromText('LINESTRING(-76.522044 36.329949,
-76.521875 36.330054,-76.521658 36.330172,-76.521413 36.330273,-76.517666 36.331101,
-76.516307 36.331427,-76.515502 36.331724,-76.514664 36.332228,-76.514336 36.332422,
-76.514075 36.332541,-76.512989 36.332949,-76.509631 36.334319,-76.508420 36.334731,
-76.506860 36.335057,-76.506263 36.335119,-76.505727 36.335112,-76.505198 36.335046,
-76.504733 36.334942,-76.503785 36.334640,-76.503451 36.334492,-76.502998 36.334240,
-76.502578 36.333963,-76.502129 36.333622,-76.501708 36.333245,-76.501068 36.332746,
-76.500606 36.332353)',4326), '389', '101', 'odd', 'Hickory Cross Rd', 'Perquimans, NC', '27919');
""".replace("\n", "")

    with open('tests/fixtures/expected_37143.csv') as file:
        csv_reader = DictReader(file, delimiter=';')
        for row in csv_reader:
            sql = csv_row_to_sql(row)
            assert sql == expected_sql
            break
