import csv
from collections import Counter
from pathlib import Path


def _load(filepath: str, delimiter: str = ",", encoding: str = "latin1"):
    with open(filepath, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]

    return headers, rows


def headers(filepath: str, **kwargs) -> list[str]:
    h, _ = _load(filepath, **kwargs)
    return h


def _resolve_column(headers: list[str], column: int | str) -> str:
    if isinstance(column, int):
        try:
            return headers[column]
        except IndexError:
            raise ValueError(f"Índice de coluna inválido: {column}")

    if column not in headers:
        raise ValueError(f"Coluna '{column}' não encontrada. Colunas: {headers}")

    return column


def count_values(filepath: str, column: int | str, **kwargs) -> Counter:
    """
    Conta quantas vezes cada valor aparece em uma coluna.
    """
    h, rows = _load(filepath, **kwargs)
    name = _resolve_column(h, column)

    return Counter(row.get(name, "").strip() for row in rows)


def repeated_values(filepath: str, column: int | str, **kwargs) -> Counter:
    counts = count_values(filepath, column, **kwargs)

    return Counter({
        value: amount
        for value, amount in counts.items()
        if value and amount > 1
    })


def total_repeated_rows(filepath: str, column: int | str, **kwargs) -> int:
    repeated = repeated_values(filepath, column, **kwargs)
    return sum(repeated.values())


def total_extra_repetitions(filepath: str, column: int | str, **kwargs) -> int:
    repeated = repeated_values(filepath, column, **kwargs)
    return sum(amount - 1 for amount in repeated.values())