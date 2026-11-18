"""PSE S.A. Rynkowa Cena Energii (RCE) API client and 48h rolling chain generator.

Fetches 15-minute RCE prices from the official public PSE S.A. API,
aggregates them into 30-minute intervals for EMHASS, applies prosumer
deposit multipliers (e.g. 1.23 for VAT), and constructs a continuous
rolling price chain.
"""

from datetime import date, datetime, timedelta
import logging
from typing import Any
import urllib.parse
import aiohttp

_LOGGER = logging.getLogger(__name__)

PSE_RCE_API_BASE = "https://api.raporty.pse.pl/api/rce-pln"


class PseRceClient:
    """Client for Polskie Sieci Elektroenergetyczne (PSE) RCE API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the PSE RCE API client."""
        self._session = session
        self._cache: dict[str, list[dict[str, Any]]] = {}
        self._cache_timestamps: dict[str, datetime] = {}

    async def async_fetch_day_rce(self, target_date: date) -> list[dict[str, Any]]:
        """Fetch 15-minute RCE records for a specific business date from PSE API."""
        date_str = target_date.strftime("%Y-%m-%d")
        now = datetime.now()

        # Check cache: 15 min TTL for today/tomorrow, 24h TTL for past days
        if date_str in self._cache:
            cache_age = (now - self._cache_timestamps.get(date_str, now)).total_seconds()
            ttl = 900 if target_date >= now.date() else 86400
            if cache_age < ttl:
                return self._cache[date_str]

        filter_q = f"business_date eq '{date_str}'"
        encoded_filter = urllib.parse.quote(filter_q)
        url = f"{PSE_RCE_API_BASE}?$filter={encoded_filter}"

        headers = {
            "User-Agent": "HomeAssistant-SmartStorageEMS/1.0",
            "Accept": "application/json",
        }

        try:
            async with self._session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    _LOGGER.warning(
                        "PSE API returned HTTP %s for %s: %s", resp.status, date_str, text
                    )
                    return []
                data = await resp.json()
                items = data.get("value", [])
                if items:
                    self._cache[date_str] = items
                    self._cache_timestamps[date_str] = now
                    _LOGGER.info("Fetched %d RCE records from PSE for %s", len(items), date_str)
                return items
        except Exception as err:
            _LOGGER.error("Failed to fetch RCE from PSE for %s: %s", date_str, err)
            return []

    @staticmethod
    def aggregate_15m_to_30m(
        day_items: list[dict[str, Any]], multiplier: float = 1.0
    ) -> list[float]:
        """Convert 96 15-min intervals into 48 30-min intervals in PLN/kWh."""
        if not day_items:
            return []

        # Sort items by dtime to ensure strictly sequential ordering
        sorted_items = sorted(day_items, key=lambda x: str(x.get("dtime", "")))

        res_30m = []
        for i in range(0, len(sorted_items) - 1, 2):
            try:
                p1 = float(sorted_items[i].get("rce_pln", 400.0))
                p2 = float(sorted_items[i + 1].get("rce_pln", 400.0))
            except (ValueError, TypeError):
                p1 = 400.0
                p2 = 400.0

            avg_mwh = (p1 + p2) / 2.0
            price_kwh = (avg_mwh / 1000.0) * multiplier
            res_30m.append(round(price_kwh, 4))

        return res_30m

    async def async_get_rolling_rce_chain(
        self,
        now_dt: datetime,
        horizon_steps: int = 96,
        multiplier: float = 1.0,
        default_price: float = 0.40,
        allow_negative: bool = True,
    ) -> list[float]:
        """Build continuous rolling 48h (or horizon_steps) price chain starting from current 30-min slot."""
        today = now_dt.date()
        tomorrow = today + timedelta(days=1)

        # 1. Fetch D+0 (today) and D+1 (tomorrow)
        d0_raw = await self.async_fetch_day_rce(today)
        d1_raw = await self.async_fetch_day_rce(tomorrow)

        d0_30m = self.aggregate_15m_to_30m(d0_raw, multiplier)
        d1_30m = self.aggregate_15m_to_30m(d1_raw, multiplier)

        # If today is empty, fallback to default_price (DST spring day has 46 slots, normal has 48)
        if not d0_30m or len(d0_30m) < 46:
            _LOGGER.warning(
                "PSE RCE: Incomplete data for today (%s, got %d slots), filling with default %.2f PLN/kWh",
                today,
                len(d0_30m),
                default_price,
            )
            d0_30m = [default_price] * 48

        # If tomorrow is not yet published, mirror today
        if not d1_30m or len(d1_30m) < 46:
            _LOGGER.debug(
                "PSE RCE: Tomorrow (%s) not yet available, mirroring today's profile", tomorrow
            )
            d1_30m = list(d0_30m)

        # Day after tomorrow (D+2): mirror tomorrow (or today)
        d2_30m = list(d1_30m)

        # Assemble full 3-day chain (3 * 48 = 144 steps)
        full_chain = d0_30m + d1_30m + d2_30m

        # Calculate current 30-minute slot offset from midnight
        slot_offset = (now_dt.hour * 2) + (1 if now_dt.minute >= 30 else 0)

        # Slice horizon starting from current slot
        sliced = full_chain[slot_offset : slot_offset + horizon_steps]

        if not allow_negative:
            sliced = [max(0.0, p) for p in sliced]

        # Ensure exact horizon length
        if len(sliced) < horizon_steps:
            pad_val = sliced[-1] if sliced else default_price
            sliced.extend([pad_val] * (horizon_steps - len(sliced)))

        return [round(float(p), 4) for p in sliced[:horizon_steps]]
