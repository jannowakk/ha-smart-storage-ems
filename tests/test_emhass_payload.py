"""Unit tests for EMHASS MPC payload builder."""

from custom_components.smart_storage_ems.emhass_client import EmhassClient


def test_build_mpc_payload_length_and_types() -> None:
    """Test that payload builder correctly formats and pads arrays to horizon."""
    horizon = 96
    pv_input = [100.0, 200.0, 300.0]
    load_input = [450.0]
    buy_prices = [0.62] * 48
    sell_prices = [0.35]

    payload = EmhassClient.build_mpc_payload(
        pv_forecast=pv_input,
        load_forecast=load_input,
        buy_prices=buy_prices,
        sell_prices=sell_prices,
        soc_init=0.45,
        soc_final=0.20,
        min_soc=0.15,
        pv_now=120.0,
        load_now=510.0,
        horizon=horizon,
        cost_function="cost",
        soc_deficit_cost=0.40,
    )

    assert payload["prediction_horizon"] == horizon
    assert len(payload["pv_power_forecast"]) == horizon
    assert len(payload["load_power_forecast"]) == horizon
    assert len(payload["load_cost_forecast"]) == horizon
    assert len(payload["prod_price_forecast"]) == horizon
    assert "cost_forecast_per_deferrable_load" not in payload

    # Step 0 should have real-time injected values
    assert payload["pv_power_forecast"][0] == 120.0
    assert payload["load_power_forecast"][0] == 510.0

    # Padded tail should have defaults
    assert payload["load_power_forecast"][-1] == 400.0
    assert payload["pv_power_forecast"][-1] == 0.0

    # Float values check
    assert payload["soc_init"] == 0.45
    assert payload["battery_minimum_state_of_charge"] == 0.15
    assert payload["battery_soc_deficit_threshold"] == 0.15
    assert payload["battery_stress_cost"] == 0.05


def test_emhass_client_headers() -> None:
    """Test that headers include Bearer token when provided."""
    client_no_token = EmhassClient("http://localhost:5000", session=None)
    assert client_no_token._get_headers() == {"Content-Type": "application/json"}

    client_with_token = EmhassClient("http://localhost:5000", session=None, token="secret_token_123")
    assert client_with_token._get_headers() == {
        "Content-Type": "application/json",
        "Authorization": "Bearer secret_token_123",
    }
