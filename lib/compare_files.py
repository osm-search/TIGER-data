"""
Compare two TIGER CSV files (old and new) line by line.

A line is identified by all its fields except the geometry (from, to,
interpolation, street, city, state, postcode). Identifiers only present in
the new file count as 'added', only present in the old file as 'deleted'.
Identifiers in both files with a different geometry count as 'changed'.

Also sums up the length of all lines (address interpolation lines, so a road
with house numbers on both sides counts twice).
"""

import math
import os
from collections import defaultdict
from dataclasses import dataclass, field

# Mean earth radius 6371.0088 km
KM_PER_DEGREE = 6371.0088 * math.pi / 180


@dataclass
class FileStats:
    """
    Line counts and lengths of one comparison (or the sum of many). The
    header line isn't counted.
    """
    added: int = 0
    deleted: int = 0
    changed: int = 0
    old_lines: int = 0
    new_lines: int = 0
    old_length_km: float = 0.0
    new_length_km: float = 0.0

    def percentage(self, count):
        """
        Returns count as percentage of the lines in the old file. If the old
        file was empty any count is 100%.
        """
        if self.old_lines == 0:
            return 100.0 if count else 0.0
        return count / self.old_lines * 100

    def length_percentage(self):
        """
        Returns the change of length as percentage of the old length. If the
        old file was empty any new length is +100%.
        """
        if self.old_length_km == 0:
            return 100.0 if self.new_length_km else 0.0
        return (self.new_length_km - self.old_length_km) / self.old_length_km * 100


@dataclass
class SummaryStats:
    """
    Totals over all compared files.
    """
    total_files: int = 0
    compared_files: int = 0
    missing_in_new: int = 0
    extra_in_new: int = 0
    totals: FileStats = field(default_factory=FileStats)


def linestring_length_km(geometry):
    """
    Returns the length of a 'LINESTRING(lon lat,lon lat,...)' in kilometers.
    Equirectangular approximation, precise enough for lines this short.
    """
    points = [
        tuple(map(float, point.split(' ')))
        for point in geometry[geometry.index('(') + 1:geometry.rindex(')')].split(',')
    ]
    lon_factor = math.cos(math.radians(points[0][1]))

    length = 0.0
    for (lon1, lat1), (lon2, lat2) in zip(points, points[1:]):
        length += math.hypot((lon2 - lon1) * lon_factor, lat2 - lat1)
    return length * KM_PER_DEGREE


class CompareFiles:
    """
    Finds and compares TIGER CSV files.
    """

    @staticmethod
    def list_csv_files(directory):
        """
        Returns a dict of filename => full path for all CSV files in directory.
        """
        return {
            name: os.path.join(directory, name)
            for name in sorted(os.listdir(directory))
            if name.endswith('.csv')
        }

    @staticmethod
    def read_lines(path):
        """
        Returns a dict of identifier => list of geometries, the number of lines
        and their total length in km. The same identifier can appear more than
        once, e.g. for discontinuous road segments.
        """
        lines = defaultdict(list)
        count = 0
        length_km = 0.0
        with open(path, encoding='utf-8') as file:
            next(file, None)  # header
            for line in file:
                line = line.rstrip('\n')
                if not line:
                    continue
                key, _, geometry = line.rpartition(';')
                lines[key].append(geometry)
                count += 1
                length_km += linestring_length_km(geometry)
        return lines, count, length_km

    def compare_one_file(self, old_path, new_path):
        """
        Returns FileStats for the two files.

        Lines with the same identifier are paired in sorted order of their
        geometries. Same as walking both files sorted, one line at a time.
        """
        old_lines, old_count, old_length_km = self.read_lines(old_path)
        new_lines, new_count, new_length_km = self.read_lines(new_path)

        stats = FileStats(old_lines=old_count, new_lines=new_count,
                          old_length_km=old_length_km, new_length_km=new_length_km)

        for key in old_lines.keys() | new_lines.keys():
            old_geometries = sorted(old_lines.get(key, []))
            new_geometries = sorted(new_lines.get(key, []))

            for old_geometry, new_geometry in zip(old_geometries, new_geometries):
                if old_geometry != new_geometry:
                    stats.changed += 1

            difference = len(new_geometries) - len(old_geometries)
            if difference > 0:
                stats.added += difference
            else:
                stats.deleted -= difference

        return stats

