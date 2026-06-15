"""
Лёгкий dev-сервер на стандартной библиотеке Python — без FastAPI/uvicorn/httpx.

Зачем он нужен:
  - проверить работу API сразу, без `pip install`;
  - запасной вариант для сред без доступа к интернету/PyPI.

Для продакшена используйте app.main (FastAPI с автоматической документацией,
валидацией параметров и т.д.) — эндпоинты идентичны.

Запуск (из папки backend):
    python3 dev_server.py
"""

import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.data import (
    BOND_BOARDS,
    DIVIDEND_YEAR,
    SECTOR_BY_SECID,
    load_bond_detail,
    load_bonds,
    load_stock_detail,
    load_stocks,
)
from app.filters import filter_bonds, filter_stocks


def _qf(params: dict, key: str):
    """Достаёт числовой query-параметр."""
    v = params.get(key, [None])[0]
    return float(v) if v is not None else None


def _qs(params: dict, key: str):
    return params.get(key, [None])[0]


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (имя метода задано BaseHTTPRequestHandler)
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path

        try:
            if path == "/api/meta":
                data = {
                    "dividend_year": DIVIDEND_YEAR,
                    "bond_boards": BOND_BOARDS,
                    "sectors": sorted(set(SECTOR_BY_SECID.values())),
                }

            elif path == "/api/bonds":
                bonds = asyncio.run(load_bonds())
                data = filter_bonds(
                    bonds,
                    yield_min=_qf(params, "yield_min"),
                    yield_max=_qf(params, "yield_max"),
                    price_min=_qf(params, "price_min"),
                    price_max=_qf(params, "price_max"),
                    maturity=_qs(params, "maturity"),
                    bond_type=_qs(params, "bond_type"),
                )

            elif path.startswith("/api/bonds/"):
                secid = path.rsplit("/", 1)[-1]
                bond = asyncio.run(load_bond_detail(secid))
                if bond is None:
                    return self._send_json({"detail": "Облигация не найдена"}, 404)
                data = bond

            elif path == "/api/stocks":
                stocks = asyncio.run(load_stocks())
                data = filter_stocks(
                    stocks,
                    yield_min=_qf(params, "yield_min"),
                    yield_max=_qf(params, "yield_max"),
                    price_min=_qf(params, "price_min"),
                    price_max=_qf(params, "price_max"),
                    sector=_qs(params, "sector"),
                )

            elif path.startswith("/api/stocks/"):
                secid = path.rsplit("/", 1)[-1]
                stock = asyncio.run(load_stock_detail(secid))
                if stock is None:
                    return self._send_json({"detail": "Акция не найдена"}, 404)
                data = stock

            else:
                return self._send_json({"detail": "Не найдено"}, 404)

        except Exception as exc:  # noqa: BLE001 — в dev-сервере отдаём текст ошибки
            return self._send_json({"detail": str(exc)}, 500)

        self._send_json(data)

    def log_message(self, fmt: str, *args) -> None:
        print("[dev_server]", fmt % args)


if __name__ == "__main__":
    PORT = 8000
    print(f"ДивиБонд dev-сервер (stdlib, без FastAPI): http://127.0.0.1:{PORT}")
    print("Эндпоинты: /api/meta /api/bonds /api/stocks /api/bonds/<SECID> /api/stocks/<SECID>")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
