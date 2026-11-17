"""Unit tests for PSE RCE client and rolling chain generator."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from custom_components.smart_storage_ems.tariffs.pse_rce import PseRceClient


def test_aggregate_15m_to_30m():
    """Test converting 15-minute intervals into 30-minute intervals."""
    # 4 intervals: 00:00-00:15 (500), 00:15-00:30 (700) -> 600 MWh = 0.6000 kWh
    # 00:30-00:45 (800), 00:45-01:00 (1000) -> 900 MWh = 0.9000 kWh
    mock_items = [
        {"dtime": "2026-11-17 00:15:00", "rce_pln": 500.0},
        {"dtime": "2026-11-17 00:30:00", "rce_pln": 700.0},
        {"dtime": "2026-11-17 00:45:00", "rce_pln": 800.0},
        {"dtime": "2026-11-17 01:00:00", "rce_pln": 1000.0},
    ]

    res = PseRceClient.aggregate_15m_to_30m(mock_items, multiplier=1.0)
    assert len(res) == 2
    assert res[0] == 0.6000
    assert res[1] == 0.9000

    # Test with deposit multiplier 1.23
    res_mult = PseRceClient.aggregate_15m_to_30m(mock_items, multiplier=1.23)
    assert res_mult[0] == round(0.6000 * 1.23, 4)
    assert res_mult[1] == round(0.9000 * 1.23, 4)


def test_aggregate_empty_returns_empty():
    """Test empty list returns empty result."""
    assert PseRceClient.aggregate_15m_to_30m([]) == []


def test_get_rolling_rce_chain_with_tomorrow_available():
    """Test rolling chain generation when both today and tomorrow are available."""
    client = PseRceClient(session=MagicMock())

    # Mock 96 items for day 0 (constant 500 PLN/MWh -> 0.5000 PLN/kWh)
    d0_items = [{"dtime": f"2026-11-17 {h:02d}:{m:02d}:00", "rce_pln": 500.0}
                for h in range(24) for m in (15, 30, 45, 0)]
    # Mock 96 items for day 1 (constant 800 PLN/MWh -> 0.8000 PLN/kWh)
    d1_items = [{"dtime": f"2026-11-18 {h:02d}:{m:02d}:00", "rce_pln": 800.0}
                for h in range(24) for m in (15, 30, 45, 0)]

    async def mock_fetch(target_date):
        if target_date.day == 17:
            return d0_items
        elif target_date.day == 18:
            return d1_items
        return []

    client.async_fetch_day_rce = mock_fetch

    # Test at 14:00 (slot offset = 14 * 2 = 28)
    now_dt = datetime(2026, 11, 17, 14, 0, 0)
    chain = asyncio.run(client.async_get_rolling_rce_chain(now_dt, horizon_steps=96, multiplier=1.0))

    assert len(chain) == 96
    # Today remaining slots: 48 - 28 = 20 slots at 0.5000
    assert chain[0] == 0.5000
    assert chain[19] == 0.5000
    # Tomorrow starts at index 20 (48 slots at 0.8000)
    assert chain[20] == 0.8000
    assert chain[67] == 0.8000
    # Day after tomorrow starts at index 68 (mirrors tomorrow at 0.8000)
    assert chain[68] == 0.8000
    assert chain[95] == 0.8000


def test_get_rolling_rce_chain_when_tomorrow_missing_mirrors_today():
    """Test rolling chain when tomorrow is not yet published (mirrors today)."""
    client = PseRceClient(session=MagicMock())

    d0_items = [{"dtime": f"2026-11-17 {h:02d}:{m:02d}:00", "rce_pln": 600.0}
                for h in range(24) for m in (15, 30, 45, 0)]

    async def mock_fetch(target_date):
        if target_date.day == 17:
            return d0_items
        return []

    client.async_fetch_day_rce = mock_fetch

    now_dt = datetime(2026, 11, 17, 10, 15, 0)  # slot offset = 20
    chain = asyncio.run(client.async_get_rolling_rce_chain(now_dt, horizon_steps=96, multiplier=1.0))

    assert len(chain) == 96
    # All slots should mirror today's 0.6000
    assert all(p == 0.6000 for p in chain)
