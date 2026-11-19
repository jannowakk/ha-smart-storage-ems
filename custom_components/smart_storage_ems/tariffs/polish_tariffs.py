"""Built-in Polish Tariffs Engine for Smart Storage EMS.

Supports:
- G13 (Tauron / Enea 3-zone tariff with winter/summer peak adjustments)
- G12w (Weekend 2-zone tariff)
- Full statutory Polish holiday & moveable feast calculation
"""

from datetime import date, datetime, timedelta
import logging

_LOGGER = logging.getLogger(__name__)


def get_easter_date(year: int) -> date:
    """Calculate Easter Sunday using Meeus/Jones/Butcher algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def is_polish_holiday(d: date) -> bool:
    """Check if given date is a Polish statutory holiday."""
    # Fixed statutory holidays
    fixed_holidays = {
        (1, 1),    # Nowy Rok
        (1, 6),    # Święto Trzech Króli
        (5, 1),    # Święto Pracy
        (5, 3),    # Święto Konstytucji 3 Maja
        (8, 15),   # Wniebowzięcie NMP
        (11, 1),   # Wszystkich Świętych
        (11, 11),  # Narodowe Święto Niepodległości
        (12, 25),  # Boże Narodzenie (dzień 1)
        (12, 26),  # Boże Narodzenie (dzień 2)
    }
    if (d.month, d.day) in fixed_holidays:
        return True

    # Moveable feasts
    easter = get_easter_date(d.year)
    easter_monday = easter + timedelta(days=1)
    corpus_christi = easter + timedelta(days=60)  # Boże Ciało

    if d in (easter, easter_monday, corpus_christi):
        return True

    return False


def is_free_day(d: date) -> bool:
    """Check if date is a weekend (Saturday, Sunday) or statutory holiday."""
    # Monday is 0, Sunday is 6
    if d.weekday() >= 5:
        return True
    return is_polish_holiday(d)


def generate_g13_chain(
    start_time: datetime,
    horizon_steps: int = 96,
    p_t1: float = 0.90,
    p_t2: float = 1.49,
    p_t3: float = 0.62,
) -> list[float]:
    """Generate rolling G13 price forecast in 30-minute intervals.

    T1: Przedpołudniowy szczyt (07:00 - 13:00) w dni robocze
    T2: Popołudniowy szczyt (zima: 16:00 - 21:00, lato: 19:00 - 22:00) w dni robocze
    T3: Pozaszczytowa dolina (pozostałe godziny + całe weekendy i święta)
    """
    minute_slot = 30 if start_time.minute >= 30 else 0
    current_step_dt = start_time.replace(minute=minute_slot, second=0, microsecond=0)

    prices: list[float] = []
    for _ in range(horizon_steps):
        dt = current_step_dt
        d = dt.date()
        hour = dt.hour
        is_winter = dt.month in (10, 11, 12, 1, 2, 3)

        if is_free_day(d):
            price = p_t3
        elif 7 <= hour < 13:
            price = p_t1
        elif (is_winter and 16 <= hour < 21) or (not is_winter and 19 <= hour < 22):
            price = p_t2
        else:
            price = p_t3

        prices.append(round(price, 2))
        current_step_dt += timedelta(minutes=30)

    return prices


def generate_g11_chain(
    start_time: datetime,
    horizon_steps: int = 96,
    p_flat: float = 0.95,
) -> list[float]:
    """Generate flat G11 price forecast in 30-minute intervals."""
    return [round(float(p_flat), 2)] * horizon_steps


def generate_g12_chain(
    start_time: datetime,
    horizon_steps: int = 96,
    p_peak: float = 1.15,
    p_offpeak: float = 0.65,
) -> list[float]:
    """Generate rolling G12 (standard day/night without weekend rules) in 30-minute intervals.

    Szczyt: 06:00-13:00 oraz 15:00-22:00 codziennie
    Pozaszczyt: 13:00-15:00 oraz 22:00-06:00 codziennie
    """
    minute_slot = 30 if start_time.minute >= 30 else 0
    current_step_dt = start_time.replace(minute=minute_slot, second=0, microsecond=0)

    prices: list[float] = []
    for _ in range(horizon_steps):
        dt = current_step_dt
        hour = dt.hour

        if (6 <= hour < 13) or (15 <= hour < 22):
            price = p_peak
        else:
            price = p_offpeak

        prices.append(round(price, 2))
        current_step_dt += timedelta(minutes=30)

    return prices


def generate_g12w_chain(
    start_time: datetime,
    horizon_steps: int = 96,
    p_peak: float = 1.15,
    p_offpeak: float = 0.65,
) -> list[float]:
    """Generate rolling G12w price forecast in 30-minute intervals.

    Szczyt: 06:00-13:00 oraz 15:00-22:00 w dni robocze
    Pozaszczyt: 13:00-15:00, 22:00-06:00 oraz całe weekendy i święta
    """
    minute_slot = 30 if start_time.minute >= 30 else 0
    current_step_dt = start_time.replace(minute=minute_slot, second=0, microsecond=0)

    prices: list[float] = []
    for _ in range(horizon_steps):
        dt = current_step_dt
        hour = dt.hour

        if is_free_day(dt.date()):
            price = p_offpeak
        elif (6 <= hour < 13) or (15 <= hour < 22):
            price = p_peak
        else:
            price = p_offpeak

        prices.append(round(price, 2))
        current_step_dt += timedelta(minutes=30)

    return prices


def generate_g12r_chain(
    start_time: datetime,
    horizon_steps: int = 96,
    p_peak: float = 1.15,
    p_offpeak: float = 0.65,
) -> list[float]:
    """Generate rolling G12r (Energa - Ekonomiczna Dolina) in 30-minute intervals.

    Wydłużony pozaszczyt: 13:00-16:00 oraz 22:00-07:00 codziennie
    Szczyt: 07:00-13:00 oraz 16:00-22:00 codziennie
    """
    minute_slot = 30 if start_time.minute >= 30 else 0
    current_step_dt = start_time.replace(minute=minute_slot, second=0, microsecond=0)

    prices: list[float] = []
    for _ in range(horizon_steps):
        dt = current_step_dt
        hour = dt.hour

        if (7 <= hour < 13) or (16 <= hour < 22):
            price = p_peak
        else:
            price = p_offpeak

        prices.append(round(price, 2))
        current_step_dt += timedelta(minutes=30)

    return prices


def generate_g12n_chain(
    start_time: datetime,
    horizon_steps: int = 96,
    p_peak: float = 1.15,
    p_offpeak: float = 0.65,
) -> list[float]:
    """Generate rolling G12n (PGE - Tania Niedziela) in 30-minute intervals.

    Dni powszednie i soboty: szczyt 06:00-13:00 oraz 15:00-22:00, pozaszczyt 13:00-15:00 i 22:00-06:00
    Niedziele i dni ustawowo wolne od pracy: cała doba pozaszczyt
    """
    minute_slot = 30 if start_time.minute >= 30 else 0
    current_step_dt = start_time.replace(minute=minute_slot, second=0, microsecond=0)

    prices: list[float] = []
    for _ in range(horizon_steps):
        dt = current_step_dt
        d = dt.date()
        hour = dt.hour

        if d.weekday() == 6 or is_polish_holiday(d):
            price = p_offpeak
        elif (6 <= hour < 13) or (15 <= hour < 22):
            price = p_peak
        else:
            price = p_offpeak

        prices.append(round(price, 2))
        current_step_dt += timedelta(minutes=30)

    return prices


def generate_g13s_chain(
    start_time: datetime,
    horizon_steps: int = 96,
    p_peak: float = 1.25,
    p_day_offpeak: float = 0.55,
    p_night: float = 0.60,
) -> list[float]:
    """Generate rolling G13s (Tauron Sezonowa OZE / Magazyny) in 30-minute intervals.

    Okres letni (1.04 - 30.09):
      - Dzienna pozaszczytowa (09:00 - 17:00): p_day_offpeak
      - Dzienna szczytowa (07:00 - 09:00, 17:00 - 21:00): p_peak
      - Nocna (21:00 - 07:00): p_night

    Okres zimowy (1.10 - 31.03):
      - Dzienna pozaszczytowa (10:00 - 15:00): p_day_offpeak
      - Dzienna szczytowa (07:00 - 10:00, 15:00 - 21:00): p_peak
      - Nocna (21:00 - 07:00): p_night
    """
    minute_slot = 30 if start_time.minute >= 30 else 0
    current_step_dt = start_time.replace(minute=minute_slot, second=0, microsecond=0)

    prices: list[float] = []
    for _ in range(horizon_steps):
        dt = current_step_dt
        hour = dt.hour
        is_summer = 4 <= dt.month <= 9

        if is_summer:
            if 9 <= hour < 17:
                price = p_day_offpeak
            elif (7 <= hour < 9) or (17 <= hour < 21):
                price = p_peak
            else:
                price = p_night
        else:
            if 10 <= hour < 15:
                price = p_day_offpeak
            elif (7 <= hour < 10) or (15 <= hour < 21):
                price = p_peak
            else:
                price = p_night

        prices.append(round(price, 2))
        current_step_dt += timedelta(minutes=30)

    return prices

