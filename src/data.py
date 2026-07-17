import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"


def iter_records(filename: str):
    """Yields (index, record) tuples from data/raw/<filename>."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"No file found at {path}")

    with open(path, encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError(f"Expected a list of objects, got {type(records).__name__}")

    for i, record in enumerate(records):
        desc = record.get("description")
        if not desc or not desc.strip():
            continue
        yield i, record


def iter_descriptions(filename: str):
    """Yields (index, description) tuples. Convenience wrapper over iter_records."""
    for i, record in iter_records(filename):
        yield i, record["description"]


def load_descriptions(filename: str) -> list[tuple[int, str]]:
    return list(iter_descriptions(filename))