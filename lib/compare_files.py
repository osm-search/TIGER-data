"""
Compare two TIGER CSV files (old and new) line by line.

A line is identified by all its fields except the geometry (from, to,
interpolation, street, city, state, postcode). Identifiers only present in
the new file count as 'added', only present in the old file as 'deleted'.
Identifiers in both files with a different geometry count as 'changed'.
"""

import os
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class FileStats:
    """
    Line counts of one comparison (or the sum of many). The header line
    isn't counted.
    """
    added: int = 0
    deleted: int = 0
    changed: int = 0
    old_lines: int = 0
    new_lines: int = 0

    def percentage(self, count):
        """
        Returns count as percentage of the lines in the old file.
        """
        if self.old_lines == 0:
            return 0.0
        return count / self.old_lines * 100


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
        Returns a dict of identifier => list of geometries. The same identifier
        can appear more than once, e.g. for discontinuous road segments.
        """
        lines = defaultdict(list)
        count = 0
        with open(path, encoding='utf-8') as file:
            next(file, None)  # header
            for line in file:
                line = line.rstrip('\n')
                if not line:
                    continue
                key, _, geometry = line.rpartition(';')
                lines[key].append(geometry)
                count += 1
        return lines, count

    def compare_one_file(self, old_path, new_path):
        """
        Returns FileStats for the two files.

        Lines with the same identifier are paired in sorted order of their
        geometries. Same as walking both files sorted, one line at a time.
        """
        old_lines, old_count = self.read_lines(old_path)
        new_lines, new_count = self.read_lines(new_path)

        stats = FileStats(old_lines=old_count, new_lines=new_count)

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

