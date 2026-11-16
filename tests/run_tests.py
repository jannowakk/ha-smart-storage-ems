#!/usr/bin/env python3
"""Standalone test runner for Smart Storage EMS."""

import sys
from unittest.mock import MagicMock

# Setup lightweight mocks for Home Assistant environment
def callback(func):
    return func

ha_mock = MagicMock()
core_mock = MagicMock()
core_mock.callback = callback

sys.modules["homeassistant"] = ha_mock
sys.modules["homeassistant.core"] = core_mock
sys.modules["homeassistant.config_entries"] = ha_mock
sys.modules["homeassistant.const"] = ha_mock
sys.modules["homeassistant.components"] = ha_mock
sys.modules["homeassistant.components.sensor"] = ha_mock
sys.modules["homeassistant.components.select"] = ha_mock
sys.modules["homeassistant.components.switch"] = ha_mock
sys.modules["homeassistant.components.button"] = ha_mock
sys.modules["homeassistant.helpers"] = ha_mock
sys.modules["homeassistant.helpers.selector"] = ha_mock
sys.modules["homeassistant.helpers.aiohttp_client"] = ha_mock
sys.modules["homeassistant.helpers.event"] = ha_mock
sys.modules["homeassistant.helpers.update_coordinator"] = ha_mock
sys.modules["homeassistant.helpers.entity_platform"] = ha_mock
sys.modules["aiohttp"] = MagicMock()

sys.path.insert(0, ".")

from tests.test_emhass_payload import test_build_mpc_payload_length_and_types
from tests.test_import_guard import (
    test_import_guard_triggers_when_exceeding_threshold,
    test_import_guard_does_not_trigger_when_battery_empty,
    test_import_guard_does_not_trigger_when_charging,
)
from tests.test_polish_tariffs import (
    test_polish_holidays,
    test_g13_chain_generation,
)

if __name__ == "__main__":
    print("Running Smart Storage EMS unit tests...")
    test_build_mpc_payload_length_and_types()
    print("✓ test_build_mpc_payload_length_and_types passed")

    test_import_guard_triggers_when_exceeding_threshold()
    print("✓ test_import_guard_triggers_when_exceeding_threshold passed")

    test_import_guard_does_not_trigger_when_battery_empty()
    print("✓ test_import_guard_does_not_trigger_when_battery_empty passed")

    test_import_guard_does_not_trigger_when_charging()
    print("✓ test_import_guard_does_not_trigger_when_charging passed")

    test_polish_holidays()
    print("✓ test_polish_holidays passed")

    test_g13_chain_generation()
    print("✓ test_g13_chain_generation passed")

    print("\nAll unit tests passed successfully!")

