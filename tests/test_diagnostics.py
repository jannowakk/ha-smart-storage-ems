"""Tests for Smart Storage EMS diagnostics and redaction."""

import unittest
from unittest.mock import MagicMock
from custom_components.smart_storage_ems.diagnostics import async_get_config_entry_diagnostics


class TestDiagnostics(unittest.IsolatedAsyncioTestCase):
    """Test diagnostics module."""

    async def test_async_get_config_entry_diagnostics(self) -> None:
        """Test compiling diagnostics with mocked coordinator and entry."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry_123"

        coordinator = MagicMock()
        coordinator.get_diagnostics_data.return_value = {
            "version": "1.3.0",
            "operation_mode": "auto_mpc",
            "configuration": {
                "emhass_url": "http://localhost:5000",
                "emhass_token": "***REDACTED***",
            },
            "entities_health": {
                "sensor.soc": {"status": "OK", "state": "90", "unit": "%"}
            },
        }

        hass.data = {
            "smart_storage_ems": {
                "test_entry_123": coordinator
            }
        }

        result = await async_get_config_entry_diagnostics(hass, entry)
        self.assertIn("version", result)
        self.assertEqual(result["version"], "1.3.0")
        self.assertEqual(result["configuration"]["emhass_token"], "***REDACTED***")
        self.assertIn("entities_health", result)


if __name__ == "__main__":
    unittest.main()
