"""
Сборка данных по облигациям и акциям.

Вынесено отдельно от main.py, чтобы:
  - не тянуть FastAPI там, где он не нужен (тесты, скрипты, бот);
  - было легко покрыть тестами и переиспользовать в боте/скриптах обновления кэша.
"""

from datetime import datetime, timedelta
from typing import Optional

from .moex_client import fetch_bonds_board, fetch_dividends, fetch_shares_board
from .parsers import table_to_dicts
from .yield_calc import bond_current_yield, dividend_yield_for_year, maturity_bucket

# Торговые доски облигаций, которые агрегируем в один список.
BOND_BOARDS = ["TQOB", "TQCB"]
BOND_TYPE_BY_BOARD = {"TQOB": "ОФЗ", "TQCB": "Корпоративная"}

# MOEX ISS не отдаёт сектор экономики в этом эндпоинте — храним сопоставление
# вручную. В реальном проекте это можно вынести в БД/конфиг.
SECTOR_BY_SECID = {
    "SBER": "Финансы",
    "LKOH": "Нефть и газ",
    "MTSS": "Телеком",
    "TATN": "Нефть и газ",
}

# Дивидендную доходность считаем по факту выплат за прошлый календарный год —
# это требование приложения ("указывай доходность только за предыдущий год").
DIVIDEND_YEAR = datetime.now().year - 1


async def load_bonds() -> list[dict]:
    bonds: list[dict] = []

    for board in BOND_BOARDS:
        raw = await fetch_bonds_board(board)
        securities = table_to_dicts(raw["securities"])
        marketdata = {row["SECID"]: row for row in table_to_dicts(raw["marketdata"])}

        for sec in securities:
            secid = sec["SECID"]
            md = marketdata.get(secid, {})
            ytm, is_floating = bond_current_yield(sec, md)

            bonds.append({
                "secid": secid,
                "name": sec.get("SHORTNAME"),
                "isin": sec.get("ISIN"),
                "type": BOND_TYPE_BY_BOARD.get(board, board),
                "price": md.get("LAST") if md.get("LAST") and md.get("LAST") > 0 else None,
                "yield": ytm if ytm and 0 < ytm < 500 else None,
                "is_floating": is_floating,
                "face_value": sec.get("FACEVALUE"),
                "coupon_percent": sec.get("COUPONPERCENT"),
                "coupon_value": sec.get("COUPONVALUE"),
                "coupon_period": sec.get("COUPONPERIOD"),
                "next_coupon": sec.get("NEXTCOUPON") if sec.get("NEXTCOUPON") not in (None, "0000-00-00", "") else None,
                "maturity": sec.get("MATDATE") if sec.get("MATDATE") not in (None, "0000-00-00", "") else None,
                "maturity_bucket": maturity_bucket(sec.get("MATDATE")),
            })

    return bonds


async def load_bond_detail(secid: str) -> Optional[dict]:
    bonds = await load_bonds()
    bond = next((b for b in bonds if b["secid"] == secid), None)
    if bond is None:
        return None

    # Прогноз ближайших купонных выплат на основе NEXTCOUPON и COUPONPERIOD.
    schedule = []
    if bond["next_coupon"] and bond["coupon_period"]:
        next_date = datetime.strptime(bond["next_coupon"], "%Y-%m-%d")
        for _ in range(3):
            schedule.append({
                "date": next_date.strftime("%Y-%m-%d"),
                "amount": bond["coupon_value"],
            })
            next_date += timedelta(days=int(bond["coupon_period"]))

    bond["upcoming_coupons"] = schedule
    return bond


async def load_stocks() -> list[dict]:
    raw = await fetch_shares_board("TQBR")
    securities = table_to_dicts(raw["securities"])
    marketdata = {row["SECID"]: row for row in table_to_dicts(raw["marketdata"])}

    stocks: list[dict] = []

    for sec in securities:
        secid = sec["SECID"]
        md = marketdata.get(secid, {})
        price = md.get("LAST")

        div_raw = await fetch_dividends(secid)
        dividends = table_to_dicts(div_raw.get("dividends", {"columns": [], "data": []}))
        div_yield = dividend_yield_for_year(dividends, price or 0, DIVIDEND_YEAR)

        stocks.append({
            "secid": secid,
            "name": sec.get("SHORTNAME"),
            "isin": sec.get("ISIN"),
            "sector": SECTOR_BY_SECID.get(secid, "Другое"),
            "price": price,
            "dividend_yield": div_yield,
            "dividend_year": DIVIDEND_YEAR,
        })

    return stocks


async def load_stock_detail(secid: str) -> Optional[dict]:
    stocks = await load_stocks()
    stock = next((s for s in stocks if s["secid"] == secid), None)
    if stock is None:
        return None

    div_raw = await fetch_dividends(secid)
    dividends = table_to_dicts(div_raw.get("dividends", {"columns": [], "data": []}))
    stock["dividends_history"] = sorted(dividends, key=lambda d: d["registryclosedate"], reverse=True)
    return stock
