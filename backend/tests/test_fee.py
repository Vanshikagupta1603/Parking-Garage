from datetime import datetime, timedelta
from decimal import Decimal

from app.fee import compute_fee, compute_hours

FIRST = Decimal("5.00")
EXTRA = Decimal("3.00")
CAP = Decimal("20.00")


def entry():
    return datetime(2026, 1, 1, 9, 0, 0)


def test_within_grace_period_is_free():
    t0 = entry()
    fee = compute_fee(t0, t0 + timedelta(minutes=5), FIRST, EXTRA, CAP)
    assert fee == Decimal("0.00")


def test_exact_grace_boundary_is_free():
    t0 = entry()
    fee = compute_fee(t0, t0 + timedelta(minutes=10), FIRST, EXTRA, CAP)
    assert fee == Decimal("0.00")


def test_just_over_grace_charges_first_hour():
    t0 = entry()
    fee = compute_fee(t0, t0 + timedelta(minutes=11), FIRST, EXTRA, CAP)
    assert fee == FIRST


def test_exact_one_hour():
    t0 = entry()
    fee = compute_fee(t0, t0 + timedelta(hours=1), FIRST, EXTRA, CAP)
    assert fee == FIRST


def test_partial_hour_rounds_up():
    t0 = entry()
    # 1 hour 1 minute must be charged as 2 hours, not 1
    fee = compute_fee(t0, t0 + timedelta(hours=1, minutes=1), FIRST, EXTRA, CAP)
    assert fee == FIRST + EXTRA


def test_daily_cap_applies():
    t0 = entry()
    # Enough hours that tiered pricing would exceed the cap
    fee = compute_fee(t0, t0 + timedelta(hours=10), FIRST, EXTRA, CAP)
    assert fee == CAP


def test_multi_day_stay_stacks_caps():
    t0 = entry()
    # 2 full days + 3 extra hours
    fee = compute_fee(t0, t0 + timedelta(days=2, hours=3), FIRST, EXTRA, CAP)
    expected = 2 * CAP + min(FIRST + 2 * EXTRA, CAP)
    assert fee == expected.quantize(Decimal("0.01"))


def test_exit_before_entry_raises():
    t0 = entry()
    try:
        compute_hours(t0, t0 - timedelta(minutes=1))
        assert False, "expected ValueError"
    except ValueError:
        pass
