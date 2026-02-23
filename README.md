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


US Postcodes
-------------
Addtionally create a `us_postcodes.csv.gz` file with centroid coordinates.

    cat output-path/*.csv | ./calculate_postcode_centroids.py | gzip -9 > us_postcodes.csv.gz


License
-------
The source code is available under a GPLv2 license.
