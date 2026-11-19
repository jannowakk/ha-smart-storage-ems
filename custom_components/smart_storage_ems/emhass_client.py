"""EMHASS REST API Client for Smart Storage EMS."""

import json
import logging
from typing import Any
import aiohttp

_LOGGER = logging.getLogger(__name__)


class EmhassClient:
    """Client for communicating with EMHASS service."""

    def __init__(
        self,
        base_url: str,
        session: aiohttp.ClientSession,
        token: str | None = None,
    ) -> None:
        """Initialize the EMHASS client."""
        # In Docker / HAOS, localhost can resolve to IPv6 ::1 where EMHASS is not listening.
        # Normalize localhost to 127.0.0.1 for maximum network reliability.
        clean_url = base_url.rstrip("/").replace("://localhost", "://127.0.0.1")
        self._base_url = clean_url
        self._session = session
        self._token = token.strip() if token else None

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with optional Bearer token."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def async_run_mpc_optimization(self, payload: dict[str, Any]) -> bool:
        """Send naive-mpc-optim request to EMHASS."""
        url = f"{self._base_url}/action/naive-mpc-optim"
        _LOGGER.debug("Sending MPC optimization request to %s", url)
        try:
            async with self._session.post(
                url,
                data=json.dumps(payload),
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=90),
            ) as response:
                if response.status in (200, 201):
                    _LOGGER.info("EMHASS MPC optimization completed successfully")
                    return True
                text = await response.text()
                _LOGGER.error("EMHASS MPC failed (status %s): %s", response.status, text)
                return False
        except Exception as err:
            _LOGGER.error("Failed to connect to EMHASS at %s: %s", url, err)
            return False

    async def async_publish_data(self) -> bool:
        """Trigger EMHASS to publish latest MPC results to Home Assistant."""
        url = f"{self._base_url}/action/publish-data"
        _LOGGER.debug("Sending publish-data request to %s", url)
        try:
            async with self._session.post(
                url,
                data=json.dumps({}),
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status in (200, 201):
                    _LOGGER.info("EMHASS published data successfully")
                    return True
                text = await response.text()
                _LOGGER.error("EMHASS publish-data failed (status %s): %s", response.status, text)
                return False
        except Exception as err:
            _LOGGER.error("Failed to connect to EMHASS publish at %s: %s", url, err)
            return False

    @staticmethod
    def build_mpc_payload(
        pv_forecast: list[float],
        load_forecast: list[float],
        buy_prices: list[float],
        sell_prices: list[float],
        soc_init: float,
        soc_final: float,
        min_soc: float,
        pv_now: float,
        load_now: float,
        horizon: int = 96,
        cost_function: str = "cost",
        soc_deficit_cost: float = 0.4,
        battery_stress_cost: float = 0.05,
    ) -> dict[str, Any]:
        """Build standard MPC payload for EMHASS."""
        # Trim or pad lists to match horizon
        def _normalize(data: list[float], default_val: float) -> list[float]:
            res = [round(float(x), 2) for x in data[:horizon]]
            if len(res) < horizon:
                res.extend([round(default_val, 2)] * (horizon - len(res)))
            return res

        pv_list = _normalize(pv_forecast, 0.0)
        load_list = _normalize(load_forecast, 400.0)
        buy_list = _normalize(buy_prices, 0.65)
        sell_list = _normalize(sell_prices, 0.40)

        # Inject real-time values for step 0
        if pv_list:
            pv_list[0] = round(pv_now, 2)
        if load_list:
            load_list[0] = round(load_now, 2)

        return {
            "pv_forecast_method": "list",
            "pv_power_forecast": pv_list,
            "load_power_forecast": load_list,
            "prod_price_forecast": sell_list,
            "load_cost_forecast": buy_list,
            "soc_init": round(soc_init, 2),
            "soc_final": round(soc_final, 2),
            "prediction_horizon": horizon,
            "weight_battery_charge": 0.01,
            "weight_battery_discharge": 0.01,
            "battery_discharge_efficiency": 0.90,
            "battery_charge_efficiency": 0.90,
            "battery_stress_cost": round(battery_stress_cost, 2),
            "costfun": cost_function,
            "battery_soc_deficit_cost": round(soc_deficit_cost, 2),
            "battery_soc_deficit_threshold": round(min_soc, 2),
            "pv_now": round(pv_now, 2),
            "load_now": round(load_now, 2),
            "battery_minimum_state_of_charge": round(min_soc, 2),
        }
