#!/usr/bin/env python3
"""Sort a CSV by a named column and remove duplicate rows.
ex: 
    python tools/sorter_and_setify.py input.csv output.csv column_name
"""

import argparse
import csv
import sys
from pathlib import Path


def sort_csv(input_file: Path, output_file: str, column: str) -> None:
	with input_file.open("r", newline="", encoding="utf-8-sig") as source:
		reader = csv.DictReader(source)
		if not reader.fieldnames:
			raise ValueError("The CSV file must contain a header row.")
		if column not in reader.fieldnames:
			raise ValueError(
				f"Unknown column {column!r}; available columns: "
				+ ", ".join(reader.fieldnames)
			)

		rows = list(reader)
		unique_rows = []
		seen = set()
		for row in rows:
			key = tuple(row.get(field, "") for field in reader.fieldnames)
			if key not in seen:
				seen.add(key)
				unique_rows.append(row)

		unique_rows.sort(key=lambda row: row.get(column, "").casefold())

	destination = sys.stdout if output_file == "-" else Path(output_file).open(
		"w", newline="", encoding="utf-8"
	)
	try:
		writer = csv.DictWriter(destination, fieldnames=reader.fieldnames)
		writer.writeheader()
		writer.writerows(unique_rows)
	finally:
		if destination is not sys.stdout:
			destination.close()


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Sort products in a CSV file and remove duplicate rows."
	)
	parser.add_argument("input", type=Path, help="Input CSV file")
	parser.add_argument("output", help="Output CSV file, or '-' for stdout")
	parser.add_argument("column", help="Column name to sort by")
	args = parser.parse_args()

	try:
		sort_csv(args.input, args.output, args.column)
	except (OSError, ValueError) as error:
		parser.error(str(error))


if __name__ == "__main__":
	main()
