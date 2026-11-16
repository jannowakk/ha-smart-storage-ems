"""Inverter driver factory."""

from typing import Any
from homeassistant.core import HomeAssistant

from .base import BaseInverter
from .goodwe import GoodWeInverter


def get_inverter_driver(hass: HomeAssistant, config: dict[str, Any]) -> BaseInverter:
    """Return the configured inverter driver."""
    inverter_type = config.get("inverter_type", "goodwe").lower()
    if inverter_type == "goodwe":
        return GoodWeInverter(hass, config)
    raise ValueError(f"Unsupported inverter type: {inverter_type}")
