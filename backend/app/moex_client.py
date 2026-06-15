"""
Клиент для MOEX ISS API.

Пытается получить данные с реального MOEX ISS API (бесплатный, без ключа).
Если запрос не удался (нет сети, таймаут, ошибка) — берёт данные из
backend/sample_data/*.json. Это позволяет:
  - разрабатывать и тестировать логику offline;
  - сразу получить рабочее приложение, когда сервер запущен с доступом в интернет.
"""

import json
from pathlib import Path
from typing import Optional

try:
    import httpx
except ImportError:  # pragma: no cover - используется при работе без httpx (офлайн/тесты)
    httpx = None

MOEX_BASE = "https://iss.moex.com/iss"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
TIMEOUT = 4.0


async def _get_json(url: str, params: Optional[dict] = None) -> Optional[dict]:
    if httpx is None:
        return None
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        # Нет сети / MOEX недоступен / таймаут — работаем на тестовых данных
        return None


def _load_sample(filename: str) -> dict:
    with open(SAMPLE_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


async def fetch_bonds_board(board: str) -> dict:
    """Список облигаций торговой доски (например, TQOB для ОФЗ, TQCB для корпоративных)."""
    url = f"{MOEX_BASE}/engines/stock/markets/bonds/boards/{board}/securities.json"
    data = await _get_json(url, {"iss.meta": "off"})
    if data is not None:
        return data
    return _load_sample(f"bonds_{board.lower()}.json")


async def fetch_shares_board(board: str = "TQBR") -> dict:
    """Список акций торговой доски (TQBR — основной режим торгов акциями)."""
    url = f"{MOEX_BASE}/engines/stock/markets/shares/boards/{board}/securities.json"
    data = await _get_json(url, {"iss.meta": "off"})
    if data is not None:
        return data
    return _load_sample(f"shares_{board.lower()}.json")


async def fetch_dividends(secid: str) -> dict:
    """История дивидендных выплат по бумаге."""
    url = f"{MOEX_BASE}/securities/{secid}/dividends.json"
    data = await _get_json(url, {"iss.meta": "off"})
    if data is not None:
        return data
    try:
        return _load_sample(f"dividends_{secid}.json")
    except FileNotFoundError:
        return {"dividends": {"columns": ["secid", "isin", "registryclosedate", "value", "currencyid"], "data": []}}
