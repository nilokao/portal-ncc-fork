import csv
from collections import Counter


def _load(filepath: str, delimiter: str = ",", encoding: str = "latin1"):
    with open(filepath, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return headers, rows


def headers(filepath: str, **kwargs) -> list[str]:
    h, _ = _load(filepath, **kwargs)
    return h


def unique_values(filepath: str, column: int | str, **kwargs) -> list:
    h, rows = _load(filepath, **kwargs)
    name = h[column] if isinstance(column, int) else column
    return sorted(set(row[name] for row in rows))


def value_counts(filepath: str, column: int | str, **kwargs) -> Counter:
    h, rows = _load(filepath, **kwargs)
    name = h[column] if isinstance(column, int) else column
    return Counter(row[name] for row in rows)