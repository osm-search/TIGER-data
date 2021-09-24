#!/usr/bin/env python3

"""
Reads CSV with header from STDIN, print SQL to STDOUT
"""

import sys
from csv import DictReader
from lib.csv2sql import csv_row_to_sql

csv_reader = DictReader(sys.stdin, delimiter=';')
for row in csv_reader:
    print(csv_row_to_sql(row))
