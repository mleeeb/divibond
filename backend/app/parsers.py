"""Преобразование табличного формата MOEX ISS ({"columns": [...], "data": [[...]]})
в удобный список словарей."""

from typing import Any


def table_to_dicts(table: dict) -> list[dict[str, Any]]:
    columns = table["columns"]
    return [dict(zip(columns, row)) for row in table["data"]]


def table_to_dict_by_key(table: dict, key: str) -> dict[str, dict[str, Any]]:
    """Как table_to_dicts, но сразу индексирует записи по полю key (например SECID)."""
    return {row[key]: row for row in table_to_dicts(table)}
