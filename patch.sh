#/bin/bash

# The 1..45 line is way off
grep -v '45;1;all;Woodfall Rd;Middlesex;MA;02478' 25017.csv > 25017.csv.tmp
mv 25017.csv.tmp 25017.csv