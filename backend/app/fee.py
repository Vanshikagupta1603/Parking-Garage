"""
Fee calculation — deliberately pure functions with no DB or I/O so they're
trivial to unit test in isolation. This is the logic to get bulletproof
before touching spot assignment.

Rules:
- First `grace_period_minutes` are free (common in real garages).
- Partial hours round UP (1hr 1min -> charged as 2 hours).
- First hour has its own rate; every additional hour is a (usually cheaper)
  flat extra rate.
- A daily cap prevents long stays from being overcharged.
- Multi-day stays are billed as (full days * daily cap) + (tiered fee for
  the remaining partial day).
"""

import math
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

GRACE_PERIOD_MINUTES = 10


def compute_hours(
    entry: datetime, exit_: datetime, grace_minutes: int = GRACE_PERIOD_MINUTES
) -> int:
    if exit_ < entry:
        raise ValueError("exit_time cannot be before entry_time")
    minutes = (exit_ - entry).total_seconds() / 60
    if minutes <= grace_minutes:
        return 0
    return max(1, math.ceil(minutes / 60))


def _tiered_fee(hours: int, first_hour_rate, extra_hour_rate, daily_cap) -> Decimal:
    if hours <= 0:
        return Decimal("0.00")
    fee = Decimal(str(first_hour_rate)) + max(0, hours - 1) * Decimal(
        str(extra_hour_rate)
    )
    return min(fee, Decimal(str(daily_cap)))


def compute_fee(
    entry: datetime,
    exit_: datetime,
    first_hour_rate,
    extra_hour_rate,
    daily_cap,
    grace_minutes: int = GRACE_PERIOD_MINUTES,
) -> Decimal:
    hours = compute_hours(entry, exit_, grace_minutes)
    if hours == 0:
        return Decimal("0.00")

    if hours <= 24:
        fee = _tiered_fee(hours, first_hour_rate, extra_hour_rate, daily_cap)
    else:
        full_days, rem_hours = divmod(hours, 24)
        fee = full_days * Decimal(str(daily_cap)) + _tiered_fee(
            rem_hours, first_hour_rate, extra_hour_rate, daily_cap
        )

    return fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
