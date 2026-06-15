"""
Расчёт показателей доходности.

Правила проекта:
  - облигации: показываем ТЕКУЩУЮ доходность (к текущей цене), а не доходность
    за прошлый год — для облигации это естественно, так как доходность к
    погашению всегда считается от актуальной цены;
  - облигации с переменным купоном: MOEX обычно не даёт по ним готовую
    доходность к погашению (поле YIELD пустое/0). В этом случае считаем
    "текущую доходность по последней выплате" и помечаем флагом is_floating —
    фронтенд обязан показать предупреждение, что доходность может измениться;
  - акции: дивидендная доходность считается ТОЛЬКО по факту выплат за
    предыдущий календарный год (по умолчанию 2025), как и требуют правила
    приложения.
"""

from datetime import date, datetime
from typing import Optional


def bond_current_yield(security: dict, marketdata: dict) -> tuple[Optional[float], bool]:
    """Возвращает (доходность_в_процентах, is_floating).

    is_floating=True означает, что MOEX не предоставил доходность к погашению
    (обычно это облигации с переменным/плавающим купоном), и значение посчитано
    приблизительно по последней известной выплате купона.
    """
    ytm = marketdata.get("YIELD")
    if ytm:
        return round(float(ytm), 2), False

    # Фоллбэк для облигаций с переменным купоном: простая текущая доходность
    # = (купон за год по последней известной ставке) / (текущая цена в рублях)
    coupon_value = security.get("COUPONVALUE")
    coupon_period = security.get("COUPONPERIOD")
    last_price = marketdata.get("LAST")
    face_value = security.get("FACEVALUE")

    if not all([coupon_value, coupon_period, last_price, face_value]):
        return None, True

    payments_per_year = 365 / coupon_period
    annual_coupon = coupon_value * payments_per_year
    price_in_rub = last_price / 100 * face_value

    if price_in_rub <= 0:
        return None, True

    return round(annual_coupon / price_in_rub * 100, 2), True


def maturity_bucket(matdate: Optional[str], today: Optional[date] = None) -> Optional[str]:
    """Классифицирует срок до погашения для фильтра:
    lt1 — до 1 года, 1to3 — 1-3 года, 3to5 — 3-5 лет, gt5 — более 5 лет."""
    if not matdate:
        return None

    today = today or date.today()
    md = datetime.strptime(matdate, "%Y-%m-%d").date()
    years = (md - today).days / 365

    if years < 1:
        return "lt1"
    if years < 3:
        return "1to3"
    if years < 5:
        return "3to5"
    return "gt5"


def dividend_yield_for_year(dividends: list[dict], current_price: float, year: int) -> float:
    """Сумма дивидендов с датой закрытия реестра в указанном году, делённая
    на текущую цену акции. По умолчанию год = предыдущий календарный год —
    именно это правило приложения по дивидендной доходности."""
    if not current_price:
        return 0.0

    total = sum(
        float(d["value"])
        for d in dividends
        if d.get("registryclosedate", "").startswith(str(year)) and d.get("value")
    )
    return round(total / current_price * 100, 2)
