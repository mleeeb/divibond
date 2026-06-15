"""
ДивиБонд API — бэкенд для Telegram Mini App.

Эндпоинты:
  GET /api/bonds            — список облигаций с фильтрами
  GET /api/bonds/{secid}     — карточка облигации с графиком купонных выплат
  GET /api/stocks           — список дивидендных акций с фильтрами
  GET /api/stocks/{secid}    — карточка акции с историей дивидендов
  GET /api/meta             — служебная информация (год расчёта дивдоходности и т.п.)

Запуск:
  cd backend && uvicorn app.main:app --reload --port 8000
"""

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .data import (
    DIVIDEND_YEAR,
    BOND_BOARDS,
    SECTOR_BY_SECID,
    load_bond_detail,
    load_bonds,
    load_stock_detail,
    load_stocks,
)
from .filters import filter_bonds, filter_stocks

app = FastAPI(title="ДивиБонд API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/meta")
async def get_meta():
    return {
        "dividend_year": DIVIDEND_YEAR,
        "bond_boards": BOND_BOARDS,
        "sectors": sorted(set(SECTOR_BY_SECID.values())),
    }


@app.get("/api/bonds")
async def get_bonds(
    yield_min: Optional[float] = Query(None, description="Минимальная текущая доходность, %"),
    yield_max: Optional[float] = Query(None, description="Максимальная текущая доходность, %"),
    price_min: Optional[float] = Query(None, description="Минимальная цена, % от номинала"),
    price_max: Optional[float] = Query(None, description="Максимальная цена, % от номинала"),
    maturity: Optional[str] = Query(None, pattern="^(all|lt1|1to3|3to5|gt5)$", description="Срок до погашения"),
    bond_type: Optional[str] = Query(None, description="ОФЗ / Корпоративная / all"),
):
    bonds = await load_bonds()
    return filter_bonds(bonds, yield_min, yield_max, price_min, price_max, maturity, bond_type)


@app.get("/api/bonds/{secid}")
async def get_bond(secid: str):
    bond = await load_bond_detail(secid)
    if bond is None:
        raise HTTPException(status_code=404, detail="Облигация не найдена")
    return bond


@app.get("/api/stocks")
async def get_stocks(
    yield_min: Optional[float] = Query(None, description="Мин. дивидендная доходность за прошлый год, %"),
    yield_max: Optional[float] = Query(None, description="Макс. дивидендная доходность за прошлый год, %"),
    price_min: Optional[float] = Query(None, description="Минимальная цена, ₽"),
    price_max: Optional[float] = Query(None, description="Максимальная цена, ₽"),
    sector: Optional[str] = Query(None, description="Сектор экономики / all"),
):
    stocks = await load_stocks()
    return filter_stocks(stocks, yield_min, yield_max, price_min, price_max, sector)


@app.get("/api/stocks/{secid}")
async def get_stock(secid: str):
    stock = await load_stock_detail(secid)
    if stock is None:
        raise HTTPException(status_code=404, detail="Акция не найдена")
    return stock
