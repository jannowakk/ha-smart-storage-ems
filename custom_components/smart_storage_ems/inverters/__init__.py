"""Inverter driver factory."""

from typing import Any
from homeassistant.core import HomeAssistant

from ..const import INVERTER_TYPE_DEYE, INVERTER_TYPE_GOODWE
from .base import BaseInverter
from .deye import DeyeInverter
from .goodwe import GoodWeInverter


def get_inverter_driver(hass: HomeAssistant, config: dict[str, Any]) -> BaseInverter:
    """Return the configured inverter driver."""
    inverter_type = config.get("inverter_type", INVERTER_TYPE_GOODWE).lower()
    if inverter_type == INVERTER_TYPE_GOODWE:
        return GoodWeInverter(hass, config)
    if inverter_type == INVERTER_TYPE_DEYE:
        return DeyeInverter(hass, config)
    raise ValueError(f"Unsupported inverter type: {inverter_type}")
