"""
Демонстрация работы основной логики бэкенда без поднятия HTTP-сервера.

Запуск (из папки backend):
    python3 test_logic.py

Так как в этой среде нет доступа к интернету, moex_client автоматически
использует тестовые данные из sample_data/ — но код полностью идентичен
тому, что выполнится при реальных запросах к MOEX ISS.
"""

import asyncio
import json

from app.data import (
    DIVIDEND_YEAR,
    load_bond_detail,
    load_bonds,
    load_stock_detail,
    load_stocks,
)
from app.filters import filter_bonds, filter_stocks


def _print_bonds_table(bonds: list[dict]) -> None:
    print(f"{'SECID':<16} {'Тип':<14} {'Цена,%':>8} {'Доход.,%':>9}  {'Срок':<6}  Плав. купон")
    for b in bonds:
        flag = "да, требует пометки" if b["is_floating"] else "—"
        print(
            f"{b['secid']:<16} {b['type']:<14} {b['price']:>8} "
            f"{b['yield']:>9} {b['maturity_bucket']:<6}  {flag}"
        )


def _print_stocks_table(stocks: list[dict]) -> None:
    print(f"{'SECID':<6} {'Сектор':<14} {'Цена,₽':>10} {'Дивдох. ' + str(DIVIDEND_YEAR) + ', %':>14}")
    for s in stocks:
        print(f"{s['secid']:<6} {s['sector']:<14} {s['price']:>10} {s['dividend_yield']:>14}")


async def main() -> None:
    print("=" * 70)
    print(f"Дивидендную доходность акций считаем по факту выплат за {DIVIDEND_YEAR} год")
    print("=" * 70)

    # --- Облигации -------------------------------------------------------
    bonds = await load_bonds()
    print("\nВсе облигации (TQOB + TQCB):")
    _print_bonds_table(bonds)

    print("\nФильтр: доходность 10-20%, срок до погашения > 5 лет")
    filtered = filter_bonds(bonds, yield_min=10, yield_max=20, maturity="gt5")
    _print_bonds_table(filtered)

    print("\nКарточка облигации с фиксированным купоном (SU26238RMFS4):")
    bond = await load_bond_detail("SU26238RMFS4")
    print(json.dumps(bond, ensure_ascii=False, indent=2))

    print("\nКарточка облигации с переменным купоном (VTBB199):")
    floating_bond = await load_bond_detail("VTBB199")
    print(json.dumps(floating_bond, ensure_ascii=False, indent=2))
    if floating_bond["is_floating"]:
        print(
            "\n>>> ВНИМАНИЕ: доходность рассчитана по последней выплате купона "
            "и может измениться при пересмотре ставки (фронтенд должен показать "
            "соответствующее предупреждение)."
        )

    # --- Акции -------------------------------------------------------------
    print("\n" + "=" * 70)
    stocks = await load_stocks()
    print("\nВсе акции (TQBR):")
    _print_stocks_table(stocks)

    print("\nФильтр: дивдоходность >= 10%, сектор 'Нефть и газ'")
    filtered_stocks = filter_stocks(stocks, yield_min=10, sector="Нефть и газ")
    _print_stocks_table(filtered_stocks)

    print("\nКарточка акции с историей дивидендов (SBER):")
    stock = await load_stock_detail("SBER")
    print(json.dumps(stock, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
