"""Smart Seasonal and Thermal Battery Reserve Manager for Smart Storage EMS."""

from datetime import datetime
import logging

_LOGGER = logging.getLogger(__name__)


class SeasonManager:
    """Calculates thermodynamic seasonal mode (zima/lato) and dynamic battery reserve."""

    def __init__(
        self,
        energy_threshold: float = 14.0,
        power_threshold: float = 1000.0,
    ) -> None:
        self.energy_threshold = energy_threshold
        self.power_threshold = power_threshold
        self.current_season = "zima"

    def determine_season(
        self,
        now_dt: datetime,
        pv_power: float,
        energy_today: float,
        energy_tomorrow: float,
    ) -> str:
        """Determine whether current system operates in 'lato' (summer) or 'zima' (winter) mode.

        1. Before 15:55: switch to 'lato' if today's forecast >= threshold and PV power >= 1000W.
        2. Between 15:55 and night valley (20:55 winter / 21:55 summer): continue 'lato' only if tomorrow is also sunny.
        3. Night: fallback to winter mode or calendar seasonal baseline.
        """
        is_winter_calendar = now_dt.month in (10, 11, 12, 1, 2, 3)
        t_now = now_dt.hour * 60 + now_dt.minute
        t_1555 = 15 * 60 + 55
        t_noc = (20 * 60 + 55) if is_winter_calendar else (21 * 60 + 55)

        # 1. Okno dzienne (do 15:55)
        if t_now < t_1555:
            if energy_today >= self.energy_threshold and pv_power >= self.power_threshold:
                self.current_season = "lato"
            elif self.current_season == "lato" and energy_today >= self.energy_threshold:
                self.current_season = "lato"
            else:
                self.current_season = "zima"

        # 2. Okno popołudniowe (15:55 do doliny nocnej)
        elif t_1555 <= t_now < t_noc:
            if (
                self.current_season == "lato"
                and energy_today >= self.energy_threshold
                and energy_tomorrow >= self.energy_threshold
            ):
                self.current_season = "lato"
            else:
                self.current_season = "zima"

        # 3. Dolina nocna
        else:
            self.current_season = "zima"

        return self.current_season

    def calculate_dynamic_min_soc(
        self,
        season: str,
        outside_temp: float | None,
        base_min_soc: float,
        storm_active: bool,
        energy_tomorrow: float,
    ) -> float:
        """Calculate dynamic battery reserve (min_soc) based on outdoor temperature, solar forecast and storms."""
        if season == "zima":
            temp = 10.0 if outside_temp is None else outside_temp
            # Mroz faktor: od 0°C (faktor=0) do -20°C (faktor=1.0)
            mroz_faktor = max(0.0, min(1.0, (0.0 - temp) / 20.0))
            val = 0.30 + 0.10 + (mroz_faktor * 0.15)

            # Ochrona przy burzach lub ciemnym jutrzejszym dniu (< 14 kWh)
            if storm_active or energy_tomorrow < self.energy_threshold:
                val = max(val, 0.35)

            # Ograniczenie górne dla zimy (maks. 65%)
            val = min(val, 0.65)
        else:
            # Tryb letni: schodzimy do bazowego DoD
            val = base_min_soc
            if storm_active:
                val = max(val, 0.30)

        final_min_soc = round(max(val, base_min_soc), 2)
        return final_min_soc
