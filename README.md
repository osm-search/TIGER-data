US TIGER address data for Nominatim
===================================

Convert [TIGER](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)/Line
dataset of the US Census Bureau to CSV files which can be imported by Nominatim. In Nominatim the created
tables are separate from OpenStreetMap tables and get queried at search time separately.


The dataset gets updated once per year. Downloading is prone to be slow (can take a full day) and converting
them can take hours as well. There's a mirror on https://downloads.opencagedata.com/public/

Replace '2025' with the current year throughout.

  1. Install the GDAL library and python bindings and the unzip tool

        ```bash
        # Ubuntu:
        sudo apt-get install python3-gdal python3-pip unzip
        ```

  2. Get the TIGER 2025 data. You will need the EDGES files
     (3,235 zip files, 11GB total).

         wget -r ftp://ftp2.census.gov/geo/tiger/TIGER2025/EDGES/


     Alternatively

        ```bash
        curl 'https://www2.census.gov/geo/tiger/TIGER2025/EDGES/' | grep -o 'tl_[^"]*.zip' | sort -u > filelist.txt
        # 3235 filelist.txt
        cat filelist.txt | sed -e 's!^!https://www2.census.gov/geo/tiger/TIGER2025/EDGES/!' | xargs -n 1 wget
        ```

  3. Convert the data into CSV files. Adjust the file paths in the scripts as needed

        ```bash
        ./convert.sh <input-path> <output-path> 2>&1 | tee convert.$$.log
        cd output-path
        ./patch.sh
        ```

  4. Maybe: package the created files
  
        ```bash
        tar -czf tiger2025-nominatim-preprocessed.csv.tar.gz *.csv
        ```


Subset for a partial import
---------------------------
If you only need a smaller geographic extract you can use `tiger_create_extract.py` to cut down
the data. By state, FIPS code or bounding box.

The script only needs Python 3. It uses nothing outside the standard library, so GDAL and the
other packages from step 1 are not required.

The input is the packaged `.tar.gz` archive (from step 4 or the mirror) or a directory of county
CSV files (the output of step 3). The output is a directory of county CSV files, which Nominatim
accepts in place of the archive:

```bash
# a single state, by abbreviation
./tiger_create_extract.py --states NY tiger.csv.tar.gz out/

# two states by FIPS code (36 = NY, 34 = NJ)
./tiger_create_extract.py --states 36,34 tiger.csv.tar.gz out/

# abbreviations and FIPS codes mix freely
./tiger_create_extract.py --states NY,34 tiger.csv.tar.gz out/

# bounding box
./tiger_create_extract.py --bbox=-74.26,40.49,-73.70,40.92 tiger.csv.tar.gz out/

# state and bounding box (faster than just bounding box)
./tiger_create_extract.py --states NY --bbox=-74.26,40.49,-73.70,40.92 tiger.csv.tar.gz out/

# import into Nominatim
nominatim add-data --tiger-data out/
```

US Postcodes
-------------
Addtionally create a `us_postcodes.csv.gz` file with centroid coordinates.

    cat output-path/*.csv | ./calculate_postcode_centroids.py | gzip -9 > us_postcodes.csv.gz


License
-------
The source code is available under a GPLv2 license.
