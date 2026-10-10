#!/usr/bin/env python3
"""Keep only selected fields in every JSON object in a document."""

import argparse
import json
import sys
from typing import Any


def clean_json(value: Any, fields: set[str]) -> Any:
	"""Recursively remove object fields not present in ``fields``."""
	if isinstance(value, dict):
		return {
			key: clean_json(item, fields)
			for key, item in value.items()
			if key in fields
		}
	if isinstance(value, list):
		return [clean_json(item, fields) for item in value]
	return value


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Keep only selected fields in every JSON object."
	)
	parser.add_argument("input", help="Input JSON file, or - for stdin")
	parser.add_argument("output", help="Output JSON file, or - for stdout")
	parser.add_argument(
		"--keep",
		nargs="+",
		required=True,
		metavar="FIELD",
		help="Field names to retain",
	)
	args = parser.parse_args()

	if args.input == "-":
		document = json.load(sys.stdin)
	else:
		with open(args.input, encoding="utf-8") as source:
			document = json.load(source)

	cleaned = clean_json(document, set(args.keep))
	if args.output == "-":
		json.dump(cleaned, sys.stdout, indent=2, ensure_ascii=False)
		sys.stdout.write("\n")
	else:
		with open(args.output, "w", encoding="utf-8") as destination:
			json.dump(cleaned, destination, indent=2, ensure_ascii=False)
			destination.write("\n")


if __name__ == "__main__":
	main()
