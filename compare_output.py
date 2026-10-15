#!/usr/bin/env python3

"""Compare CSV files in two directories and report differences.

Script takes two paths, each usually containing 3000 CSV files, then compares
each file, find missing and new files, then prints a summary.

"""

import argparse
import sys

from lib.compare_files import CompareFiles, SummaryStats


def existing_directory(value):
    """Argparse type that validates *value* is an existing directory."""

    from pathlib import Path

    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {value}")
    return str(path)


def non_negative_int(value):
    """Argparse type that ensures *value* is a non-negative integer."""

    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--max-files must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("--max-files must be non-negative")
    return parsed


def main(argv):
    parser = argparse.ArgumentParser(
        description="Compare CSV files between two directories.",
    )
    parser.add_argument(
        "old_dir",
        type=existing_directory,
        help="Path to the directory with the original CSV files",
    )
    parser.add_argument(
        "new_dir",
        type=existing_directory,
        help="Path to the directory with the updated CSV files",
    )
    parser.add_argument(
        "--max-files",
        type=non_negative_int,
        default=None,
        metavar="N",
        help="Limit comparison to the first N files (after sorting by name).",
    )

    args = parser.parse_args(argv)
    old_dir = args.old_dir
    new_dir = args.new_dir

    comparer = CompareFiles()
    old_files = comparer.list_csv_files(old_dir)
    new_files = comparer.list_csv_files(new_dir)

    old_names = set(old_files)
    new_names = set(new_files)

    missing_in_new = sorted(old_names - new_names)
    extra_in_new = sorted(new_names - old_names)

    for name in missing_in_new:
        print(f"Missing in new directory: {name}")
    for name in extra_in_new:
        print(f"Extra file in new directory: {name}")

    intersection = sorted(old_names & new_names)
    if args.max_files is not None:
        intersection = intersection[: args.max_files]

    summary = SummaryStats()
    summary.total_files = len(old_names)
    summary.compared_files = len(intersection)
    summary.missing_in_new = len(missing_in_new)
    summary.extra_in_new = len(extra_in_new)

    for name in intersection:
        stats = comparer.compare_one_file(old_files[name], new_files[name])
        added_pct = stats.percentage(stats.added)
        deleted_pct = stats.percentage(stats.deleted)
        changed_pct = stats.percentage(stats.changed)
        print(
            f"{name}: "
            f"added {stats.added} ({added_pct:.2f}%), "
            f"deleted {stats.deleted} ({deleted_pct:.2f}%), "
            f"changed {stats.changed} ({changed_pct:.2f}%), "
            f"length {stats.old_length_km:.1f} km -> {stats.new_length_km:.1f} km "
            f"({stats.length_percentage():+.2f}%)"
        )

        summary.totals.added += stats.added
        summary.totals.deleted += stats.deleted
        summary.totals.changed += stats.changed
        summary.totals.old_lines += stats.old_lines
        summary.totals.new_lines += stats.new_lines
        summary.totals.old_length_km += stats.old_length_km
        summary.totals.new_length_km += stats.new_length_km

    totals = summary.totals
    added_pct = totals.percentage(totals.added)
    deleted_pct = totals.percentage(totals.deleted)
    changed_pct = totals.percentage(totals.changed)

    print("\nSummary:")
    print(f"  Total files (old): {summary.total_files}")
    print(f"  Compared files: {summary.compared_files}")
    print(f"  Missing in new: {summary.missing_in_new}")
    print(f"  Extra in new: {summary.extra_in_new}")
    print(f"  Total lines (old): {totals.old_lines}")
    print(f"  Total lines (new): {totals.new_lines}")
    print(f"  Added lines: {totals.added} ({added_pct:.2f}%)")
    print(f"  Deleted lines: {totals.deleted} ({deleted_pct:.2f}%)")
    print(f"  Changed lines: {totals.changed} ({changed_pct:.2f}%)")
    print(f"  Total length (old): {totals.old_length_km:.1f} km")
    print(f"  Total length (new): {totals.new_length_km:.1f} km")
    print(f"  Length change: {totals.new_length_km - totals.old_length_km:+.1f} km "
          f"({totals.length_percentage():+.2f}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))