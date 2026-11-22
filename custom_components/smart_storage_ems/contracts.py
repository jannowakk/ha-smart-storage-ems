"""Generic Semantic Contracts and Domain Validation for Smart Storage EMS.

Defines physical domains, contract constraints, and heuristic validation
to detect cross-assignment configuration errors (e.g. price sensor in load forecast,
kW vs W scaling, monetary units in power fields, scalar vs vector mismatch).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CONF_BINARY_SENSOR_OFFGRID,
    CONF_BUY_PRICE_ATTR,
    CONF_BUY_PRICE_ENTITY,
    CONF_LOAD_FORECAST_ATTR,
    CONF_LOAD_FORECAST_ENTITY,
    CONF_NUMBER_EMS_POWER_LIMIT,
    CONF_NUMBER_EXPORT_LIMIT,
    CONF_OUTSIDE_TEMP_ENTITY,
    CONF_PV_ENERGY_TODAY_ENTITY,
    CONF_PV_ENERGY_TOMORROW_ENTITY,
    CONF_PV_FORECAST_ATTR,
    CONF_PV_FORECAST_ENTITY,
    CONF_SELECT_EMS_MODE,
    CONF_SELECT_INVERTER_MODE,
    CONF_SELL_PRICE_ATTR,
    CONF_SELL_PRICE_ENTITY,
    CONF_SENSOR_BATTERY_POWER,
    CONF_SENSOR_GRID_IMPORT,
    CONF_SENSOR_LOAD_POWER,
    CONF_SENSOR_PV_POWER,
    CONF_SENSOR_SOC,
)

_LOGGER = logging.getLogger(__name__)


class DomainType(str, Enum):
    """Physical domain classifications for entities."""

    POWER = "power"                        # Instantaneous power (W, kW)
    ENERGY = "energy"                      # Cumulative energy (kWh, MWh, Wh)
    BATTERY_SOC = "battery_soc"            # State of Charge (%, 0-100 or 0-1)
    MONETARY_PRICE = "monetary_price"      # Energy price (PLN/kWh, zł/kWh, etc.)
    TEMPERATURE = "temperature"            # Temperature (°C)
    VECTOR_POWER = "vector_power"          # 24-96 slot power forecast array in Watts
    VECTOR_PRICE = "vector_price"          # 24-96 slot energy price forecast array in PLN/kWh
    BINARY = "binary"                      # Binary on/off state
    ACTUATOR_SELECT = "actuator_select"    # Inverter/EMS select entity
    ACTUATOR_NUMBER = "actuator_number"    # Inverter/EMS number entity


@dataclass
class ValidationResult:
    """Outcome of validating an entity against a semantic contract."""

    status: str                            # "OK", "WARNING", "CRITICAL", "NOT_FOUND"
    issue: str | None = None               # Human-readable explanation of error or mismatch
    unit: str | None = None
    state: Any = None
    device_class: str | None = None
    raw_details: dict[str, Any] | None = None
    last_updated: str | None = None


@dataclass
class EntityContract:
    """Contract specifying physical, structural and semantic rules for an entity."""

    conf_key: str
    label: str
    domain_type: DomainType
    expected_ha_domains: list[str] = field(default_factory=lambda: ["sensor"])
    attr_conf_key: str | None = None
    default_attr: str | None = None
    allowed_device_classes: list[str] = field(default_factory=list)
    forbidden_device_classes: list[str] = field(default_factory=list)
    allowed_units: list[str] = field(default_factory=list)
    forbidden_unit_substrings: list[str] = field(default_factory=list)
    collision_keywords: list[str] = field(default_factory=list)
    is_vector: bool = False
    is_critical: bool = False
    min_vector_len: int = 0
    plausible_scalar_range: tuple[float, float] = (-float("inf"), float("inf"))
    plausible_vector_max_min: float = 0.0  # Vector max must be at least this value

    def validate(self, hass: HomeAssistant, config: dict[str, Any]) -> tuple[str, ValidationResult]:
        """Validate configured entity against this contract."""
        ent_id = config.get(self.conf_key)
        if not ent_id:
            return ent_id or "", ValidationResult(status="NOT_CONFIGURED")

        st = hass.states.get(ent_id)
        if st is None:
            return ent_id, ValidationResult(
                status="NOT_FOUND",
                issue=f"Encja {ent_id} nie istnieje w Home Assistant!",
            )

        val = st.state
        unit = st.attributes.get("unit_of_measurement")
        device_class = st.attributes.get("device_class")
        ent_lower = ent_id.lower()
        raw_details: dict[str, Any] | None = None

        last_updated_str = st.last_updated.isoformat() if getattr(st, "last_updated", None) else None

        # 1. Availability check
        if val in ("unavailable", "unknown"):
            return ent_id, ValidationResult(
                status="WARNING",
                issue=f"Encja w stanie niedostępnym ({val})",
                unit=unit,
                state=val,
                device_class=device_class,
                last_updated=last_updated_str,
            )

        # 2. HA Domain check (sensor vs number vs select vs binary_sensor)
        ent_domain = ent_id.split(".")[0]
        if self.expected_ha_domains and ent_domain not in self.expected_ha_domains:
            return ent_id, ValidationResult(
                status="WARNING",
                issue=f"Nieprawidłowa domena '{ent_domain}'! Oczekiwano domeny z listy: {self.expected_ha_domains}",
                unit=unit,
                state=val,
                device_class=device_class,
            )

        # 3. Device Class collision check
        if device_class and self.forbidden_device_classes:
            if device_class.lower() in [dc.lower() for dc in self.forbidden_device_classes]:
                return ent_id, ValidationResult(
                    status="CRITICAL",
                    issue=(
                        f"Kolizja semantyczna! Encja ma klasę '{device_class}', "
                        f"która jest zabroniona dla domeny '{self.domain_type.value}'!"
                    ),
                    unit=unit,
                    state=val,
                    device_class=device_class,
                )

        # 4. Unit collision check
        unit_str = str(unit or "").lower()
        if unit_str and self.forbidden_unit_substrings:
            for forbidden_sub in self.forbidden_unit_substrings:
                if forbidden_sub.lower() in unit_str:
                    return ent_id, ValidationResult(
                        status="CRITICAL",
                        issue=(
                            f"Niezgodność jednostki! Encja raportuje '{unit}', co wskazuje na dane "
                            f"niezgodne z domeną '{self.domain_type.value}' (np. waluta zamiast mocy)."
                        ),
                        unit=unit,
                        state=val,
                        device_class=device_class,
                    )

        # 5. kW vs W auto-scaling warning for power domains
        if self.domain_type in (DomainType.POWER, DomainType.VECTOR_POWER):
            if unit_str in ("kw", "kilowatt"):
                return ent_id, ValidationResult(
                    status="WARNING",
                    issue="Wykryto jednostkę 'kW' zamiast 'W' – wartości wymagają przeskalowania (x1000).",
                    unit=unit,
                    state=val,
                    device_class=device_class,
                )

        # 6. Keyword collision check (Heuristic cross-domain error detection)
        if self.collision_keywords:
            for kw in self.collision_keywords:
                if kw in ent_lower:
                    return ent_id, ValidationResult(
                        status="CRITICAL",
                        issue=(
                            f"Podejrzenie omyłkowego przypisania encji! Nazwa '{ent_id}' zawiera "
                            f"słowo kluczowe '{kw}', sugerujące inną domenę niż '{self.domain_type.value}'."
                        ),
                        unit=unit,
                        state=val,
                        device_class=device_class,
                    )

        # 7. Structural Vector Validation (for VECTOR_POWER and VECTOR_PRICE)
        if self.is_vector:
            attr_name = config.get(self.attr_conf_key) if self.attr_conf_key else self.default_attr
            cand = None
            if attr_name:
                cand = st.attributes.get(attr_name)
            if cand is None and hasattr(st, "attributes"):
                cand = st.attributes.get("forecasts") or st.attributes.get("list")

            if not isinstance(cand, list):
                # Attempt to parse json state
                try:
                    cand = json.loads(val)
                except (ValueError, TypeError, json.JSONDecodeError):
                    cand = None

            if not isinstance(cand, list):
                return ent_id, ValidationResult(
                    status="WARNING",
                    issue=f"Encja istnieje, ale nie zawiera atrybutu wektora ani listy JSON (szukano '{attr_name}')!",
                    unit=unit,
                    state=val,
                    device_class=device_class,
                )

            num_vals = [float(x) for x in cand if isinstance(x, (int, float)) and x is not None]
            raw_details = {
                "attribute": attr_name,
                "type": "list",
                "count": len(cand),
                "sample_first_4": cand[:4],
                "sample_last_4": cand[-4:],
                "min": round(min(num_vals), 2) if num_vals else None,
                "max": round(max(num_vals), 2) if num_vals else None,
            }

            if len(cand) < self.min_vector_len:
                return ent_id, ValidationResult(
                    status="WARNING",
                    issue=f"Atrybut wektora ma tylko {len(cand)} próbek (oczekiwano min. {self.min_vector_len})!",
                    unit=unit,
                    state=val,
                    device_class=device_class,
                    raw_details=raw_details,
                )

            # Plausibility check for Vector Power:
            # If max value in the entire forecast vector is < 15.0, it cannot be house power in Watts!
            if self.domain_type == DomainType.VECTOR_POWER and num_vals:
                max_v = max(num_vals)
                if max_v < self.plausible_vector_max_min:
                    return ent_id, ValidationResult(
                        status="CRITICAL",
                        issue=(
                            f"Nierealistyczne wartości wektora mocy! Maksymalna wartość wynosi zaledwie {max_v:.2f} W. "
                            f"To niemal na pewno są ceny energii w zł lub wartości w kW bez przeliczenia na W."
                        ),
                        unit=unit,
                        state=val,
                        device_class=device_class,
                        raw_details=raw_details,
                    )
                if min(num_vals) < 0.0 and self.conf_key == CONF_LOAD_FORECAST_ENTITY:
                    return ent_id, ValidationResult(
                        status="WARNING",
                        issue=f"Wektor zużycia domu zawiera ujemne wartości mocy (min: {min(num_vals):.1f} W)!",
                        unit=unit,
                        state=val,
                        device_class=device_class,
                        raw_details=raw_details,
                    )

            # Plausibility check for Vector Price:
            # If max value > 10.0 PLN/kWh, user likely passed power in Watts!
            if self.domain_type == DomainType.VECTOR_PRICE and num_vals:
                max_p = max(num_vals)
                if max_p > 10.0:
                    return ent_id, ValidationResult(
                        status="CRITICAL",
                        issue=(
                            f"Nierealistycznie wysoka cena energii! Maksymalna wartość to {max_p:.2f} PLN/kWh. "
                            f"Prawdopodobnie podłączono sensor mocy w Watach zamiast cen."
                        ),
                        unit=unit,
                        state=val,
                        device_class=device_class,
                        raw_details=raw_details,
                    )

        # 8. Scalar Sanity Check
        if not self.is_vector:
            try:
                num_val = float(val)
                min_p, max_p = self.plausible_scalar_range
                if num_val < min_p or num_val > max_p:
                    return ent_id, ValidationResult(
                        status="WARNING",
                        issue=f"Wartość {num_val} wykracza poza spodziewany fizyczny zakres ({min_p} .. {max_p})!",
                        unit=unit,
                        state=val,
                        device_class=device_class,
                    )
            except (ValueError, TypeError):
                # Not a float, ok for select/string entities
                pass

        return ent_id, ValidationResult(
            status="OK",
            unit=unit,
            state=val,
            device_class=device_class,
            raw_details=raw_details,
        )


# ==============================================================================
# REJESTR KONTRAKTÓW DLA WSZYSTKICH PÓL INTEGRACJI
# ==============================================================================

CONTRACT_REGISTRY: list[EntityContract] = [
    # 1. SoC Baterii (Krytyczne)
    EntityContract(
        conf_key=CONF_SENSOR_SOC,
        label="SoC Baterii",
        domain_type=DomainType.BATTERY_SOC,
        is_critical=True,
        allowed_device_classes=["battery"],
        forbidden_device_classes=["monetary", "power"],
        allowed_units=["%"],
        forbidden_unit_substrings=["pln", "zł", "w", "kw"],
        plausible_scalar_range=(0.0, 100.0),
        collision_keywords=["price", "cena", "taryfa", "grid_import"],
    ),
    # 2. Moc PV (Krytyczne)
    EntityContract(
        conf_key=CONF_SENSOR_PV_POWER,
        label="Moc PV",
        domain_type=DomainType.POWER,
        is_critical=True,
        allowed_device_classes=["power"],
        forbidden_device_classes=["monetary", "energy"],
        allowed_units=["W", "kW", "VA"],
        forbidden_unit_substrings=["pln", "zł", "/kwh", "kwh"],
        plausible_scalar_range=(0.0, 35000.0),
        collision_keywords=["price", "cena", "taryfa", "energy_today", "energy_total"],
    ),
    # 3. Moc Domu (Load Power - Krytyczne)
    EntityContract(
        conf_key=CONF_SENSOR_LOAD_POWER,
        label="Moc Domu",
        domain_type=DomainType.POWER,
        is_critical=True,
        allowed_device_classes=["power"],
        forbidden_device_classes=["monetary", "energy"],
        allowed_units=["W", "kW", "VA"],
        forbidden_unit_substrings=["pln", "zł", "/kwh", "kwh"],
        plausible_scalar_range=(0.0, 35000.0),
        collision_keywords=["price", "cena", "taryfa", "energy"],
    ),
    # 4. Import z Sieci (Krytyczne)
    EntityContract(
        conf_key=CONF_SENSOR_GRID_IMPORT,
        label="Import z Sieci",
        domain_type=DomainType.POWER,
        is_critical=True,
        allowed_device_classes=["power"],
        forbidden_device_classes=["monetary", "energy"],
        allowed_units=["W", "kW", "VA"],
        forbidden_unit_substrings=["pln", "zł", "/kwh", "kwh"],
        plausible_scalar_range=(0.0, 40000.0),
        collision_keywords=["price", "cena", "taryfa"],
    ),
    # 5. Moc Baterii (Krytyczne)
    EntityContract(
        conf_key=CONF_SENSOR_BATTERY_POWER,
        label="Moc Baterii",
        domain_type=DomainType.POWER,
        is_critical=True,
        allowed_device_classes=["power"],
        forbidden_device_classes=["monetary", "energy"],
        allowed_units=["W", "kW", "VA"],
        forbidden_unit_substrings=["pln", "zł", "/kwh"],
        plausible_scalar_range=(-20000.0, 20000.0),
        collision_keywords=["price", "cena", "taryfa"],
    ),
    # 6. Temperatura Zewnętrzna
    EntityContract(
        conf_key=CONF_OUTSIDE_TEMP_ENTITY,
        label="Temperatura Zewnętrzna",
        domain_type=DomainType.TEMPERATURE,
        allowed_device_classes=["temperature"],
        forbidden_device_classes=["power", "energy", "monetary"],
        allowed_units=["°C", "°F", "K"],
        forbidden_unit_substrings=["w", "kw", "pln", "zł"],
        plausible_scalar_range=(-45.0, 55.0),
    ),
    # 7. Sensor Off-Grid
    EntityContract(
        conf_key=CONF_BINARY_SENSOR_OFFGRID,
        label="Sensor Off-Grid",
        domain_type=DomainType.BINARY,
        expected_ha_domains=["binary_sensor", "input_boolean"],
    ),
    # 8. Wektor Prognozy PV
    EntityContract(
        conf_key=CONF_PV_FORECAST_ENTITY,
        label="Prognoza PV (wektor)",
        domain_type=DomainType.VECTOR_POWER,
        attr_conf_key=CONF_PV_FORECAST_ATTR,
        default_attr="list",
        is_vector=True,
        min_vector_len=24,
        plausible_vector_max_min=15.0,
        forbidden_device_classes=["monetary"],
        forbidden_unit_substrings=["pln", "zł", "eur", "usd", "/kwh"],
        collision_keywords=["price", "cena", "taryfa", "rce", "cost", "g13_standard", "g12_standard"],
    ),
    # 9. Wektor Prognozy Zużycia (House Load)
    EntityContract(
        conf_key=CONF_LOAD_FORECAST_ENTITY,
        label="Prognoza Zużycia (wektor)",
        domain_type=DomainType.VECTOR_POWER,
        attr_conf_key=CONF_LOAD_FORECAST_ATTR,
        default_attr="list",
        is_vector=True,
        min_vector_len=24,
        plausible_vector_max_min=15.0,  # Max load in vector must be >= 15 W (not prices like 0.35 - 1.5 zł)
        forbidden_device_classes=["monetary"],
        forbidden_unit_substrings=["pln", "zł", "eur", "usd", "/kwh"],
        collision_keywords=["price", "cena", "ceny", "taryfa", "taryfy", "rce", "cost", "koszt", "g13_standard", "g12_standard"],
    ),
    # 10. Ceny Zakupu (Buy Price)
    EntityContract(
        conf_key=CONF_BUY_PRICE_ENTITY,
        label="Ceny Zakupu",
        domain_type=DomainType.VECTOR_PRICE,
        attr_conf_key=CONF_BUY_PRICE_ATTR,
        default_attr="prices",
        is_vector=True,
        min_vector_len=24,
        forbidden_device_classes=["power", "energy", "battery", "temperature"],
        forbidden_unit_substrings=["kw", "kwh", "mwh"],
        collision_keywords=["consumption", "zuzycie", "load_power", "house_consumption", "pv_power"],
    ),
    # 11. Ceny Sprzedaży (Sell Price)
    EntityContract(
        conf_key=CONF_SELL_PRICE_ENTITY,
        label="Ceny Sprzedaży",
        domain_type=DomainType.VECTOR_PRICE,
        attr_conf_key=CONF_SELL_PRICE_ATTR,
        default_attr="prices",
        is_vector=True,
        min_vector_len=24,
        forbidden_device_classes=["power", "energy", "battery", "temperature"],
        forbidden_unit_substrings=["kw", "kwh", "mwh"],
        collision_keywords=["consumption", "zuzycie", "load_power", "house_consumption", "pv_power"],
    ),
    # 12. Energia PV Dziś
    EntityContract(
        conf_key=CONF_PV_ENERGY_TODAY_ENTITY,
        label="Energia PV Dziś",
        domain_type=DomainType.ENERGY,
        allowed_device_classes=["energy"],
        forbidden_device_classes=["power", "monetary"],
        allowed_units=["kWh", "Wh", "MWh"],
        plausible_scalar_range=(0.0, 200.0),
    ),
    # 13. Energia PV Jutro
    EntityContract(
        conf_key=CONF_PV_ENERGY_TOMORROW_ENTITY,
        label="Energia PV Jutro",
        domain_type=DomainType.ENERGY,
        allowed_device_classes=["energy"],
        forbidden_device_classes=["power", "monetary"],
        allowed_units=["kWh", "Wh", "MWh"],
        plausible_scalar_range=(0.0, 200.0),
    ),
    # 14-17. Encje Sterujące Falownikiem (Krytyczne dla sterowania)
    EntityContract(
        conf_key=CONF_SELECT_EMS_MODE,
        label="Tryb EMS",
        domain_type=DomainType.ACTUATOR_SELECT,
        is_critical=True,
        expected_ha_domains=["select"],
    ),
    EntityContract(
        conf_key=CONF_SELECT_INVERTER_MODE,
        label="Tryb Inwertera",
        domain_type=DomainType.ACTUATOR_SELECT,
        is_critical=True,
        expected_ha_domains=["select"],
    ),
    EntityContract(
        conf_key=CONF_NUMBER_EMS_POWER_LIMIT,
        label="Limit Mocy EMS",
        domain_type=DomainType.ACTUATOR_NUMBER,
        expected_ha_domains=["number"],
    ),
    EntityContract(
        conf_key=CONF_NUMBER_EXPORT_LIMIT,
        label="Limit Eksportu",
        domain_type=DomainType.ACTUATOR_NUMBER,
        expected_ha_domains=["number"],
    ),
]


def validate_all_entities(hass: HomeAssistant, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Execute contract validation for all configured entities in Smart Storage EMS."""
    results: dict[str, dict[str, Any]] = {}
    for contract in CONTRACT_REGISTRY:
        ent_id = config.get(contract.conf_key)
        if not ent_id:
            continue
        _, res = contract.validate(hass, config)
        results[ent_id] = {
            "label": contract.label,
            "status": res.status,
            "state": res.state,
            "unit": res.unit,
            "device_class": res.device_class,
            "issue": res.issue,
            "raw_attribute": res.raw_details,
            "last_updated": res.last_updated,
        }
    return results


def get_critical_configuration_errors(hass: HomeAssistant, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Audit critical/required entities. Returns list of blocking configuration errors.

    If any critical entity fails validation (NOT_FOUND, CRITICAL, or unavailable),
    the integration must engage Safety Halt: stop sending commands to inverter and
    display a clear blocking error to the user.
    """
    errors: list[dict[str, Any]] = []
    for contract in CONTRACT_REGISTRY:
        if not contract.is_critical:
            continue
        ent_id = config.get(contract.conf_key)
        if not ent_id:
            errors.append({
                "conf_key": contract.conf_key,
                "label": contract.label,
                "entity_id": "",
                "status": "NOT_CONFIGURED",
                "issue": f"Wymagane pole '{contract.label}' nie zostało skonfigurowane!",
            })
            continue

        _, res = contract.validate(hass, config)
        if res.status in ("CRITICAL", "NOT_FOUND"):
            errors.append({
                "conf_key": contract.conf_key,
                "label": contract.label,
                "entity_id": ent_id,
                "status": res.status,
                "issue": res.issue or "Krytyczne naruszenie kontraktu semantycznego encji!",
            })
        elif res.status == "WARNING" and res.state in ("unavailable", "unknown"):
            errors.append({
                "conf_key": contract.conf_key,
                "label": contract.label,
                "entity_id": ent_id,
                "status": "UNAVAILABLE",
                "issue": f"Wymagana encja '{contract.label}' ({ent_id}) jest niedostępna (stan: {res.state})!",
            })
    return errors
