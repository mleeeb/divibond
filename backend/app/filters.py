"""Фильтрация списков облигаций и акций — соответствует полям экрана "Фильтры"
в мини-приложении."""

from typing import Optional


def filter_bonds(
    bonds: list[dict],
    yield_min: Optional[float] = None,
    yield_max: Optional[float] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    maturity: Optional[str] = None,
    bond_type: Optional[str] = None,
) -> list[dict]:
    result = []
    for b in bonds:
        if yield_min is not None and (b["yield"] is None or b["yield"] < yield_min):
            continue
        if yield_max is not None and (b["yield"] is None or b["yield"] > yield_max):
            continue
        if price_min is not None and (b["price"] is None or b["price"] < price_min):
            continue
        if price_max is not None and (b["price"] is None or b["price"] > price_max):
            continue
        if maturity and maturity != "all" and b["maturity_bucket"] != maturity:
            continue
        if bond_type and bond_type != "all" and b["type"] != bond_type:
            continue
        result.append(b)
    return result


def filter_stocks(
    stocks: list[dict],
    yield_min: Optional[float] = None,
    yield_max: Optional[float] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    sector: Optional[str] = None,
) -> list[dict]:
    result = []
    for s in stocks:
        if yield_min is not None and s["dividend_yield"] < yield_min:
            continue
        if yield_max is not None and s["dividend_yield"] > yield_max:
            continue
        if price_min is not None and (s["price"] is None or s["price"] < price_min):
            continue
        if price_max is not None and (s["price"] is None or s["price"] > price_max):
            continue
        if sector and sector != "all" and s["sector"] != sector:
            continue
        result.append(s)
    return result
