"""
day_night_cycle.py

Part 1/4

Canonical Martian day/night cycle.

Responsible for

- time of day
- sunlight intensity
- solar efficiency
- ambient temperature modifier
- colony lighting state

Used by

- Solar Arrays
- Weather
- Power System
- Agriculture
"""

from __future__ import annotations

from dataclasses import dataclass
import math

# ============================================================
# Day / Night Cycle
# ============================================================


@dataclass
class DayNightCycle:

    sol_length: int = 24 * 60 + 39

    minute: int = 0

    fractional_minute: float = 0.0

    sunlight: float = 1.0

    solar_efficiency: float = 1.0

    temperature_modifier: float = 0.0

    daylight: bool = True

    sunrise: int = 360

    sunset: int = 1080

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
        minutes: float = 1.0,
    ) -> None:

        self.fractional_minute += max(0.0, float(minutes))
        whole_minutes = int(self.fractional_minute)
        if whole_minutes:
            self.minute = (self.minute + whole_minutes) % self.sol_length
            self.fractional_minute -= whole_minutes

        self._update()

    def hourly_update(
        self,
    ) -> None:

        self.step()

    def daily_update(
        self,
    ) -> None:

        pass

    # ========================================================
    # Internal
    # ========================================================

    def _update(
        self,
    ) -> None:

        self.daylight = self.sunrise <= self.minute <= self.sunset

        if self.daylight:

            phase = (self.minute - self.sunrise) / (self.sunset - self.sunrise)

            self.sunlight = max(
                0.0,
                math.sin(phase * math.pi),
            )

        else:

            self.sunlight = 0.0

        self.solar_efficiency = self.sunlight

        self.temperature_modifier = -40.0 + self.sunlight * 25.0

    # ========================================================
    # Queries
    # ========================================================

    @property
    def hour(
        self,
    ) -> float:

        return self.minute / 60.0

    @property
    def is_day(
        self,
    ) -> bool:

        return self.daylight

    @property
    def is_night(
        self,
    ) -> bool:

        return not self.daylight

    @property
    def is_sunrise(
        self,
    ) -> bool:

        return abs(self.minute - self.sunrise) <= 30

    @property
    def is_sunset(
        self,
    ) -> bool:

        return abs(self.minute - self.sunset) <= 30

    @property
    def light_level(
        self,
    ) -> float:

        return self.sunlight

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        return {
            "minute": self.minute,
            "fractional_minute": self.fractional_minute,
            "hour": round(
                self.hour,
                2,
            ),
            "daylight": self.daylight,
            "sunlight": round(
                self.sunlight,
                3,
            ),
            "solar_efficiency": round(
                self.solar_efficiency,
                3,
            ),
            "temperature_modifier": round(
                self.temperature_modifier,
                2,
            ),
            "sunrise": self.sunrise,
            "sunset": self.sunset,
        }

        # ========================================================

    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        return {
            "sol_length": self.sol_length,
            "minute": self.minute,
            "sunlight": self.sunlight,
            "solar_efficiency": self.solar_efficiency,
            "temperature_modifier": self.temperature_modifier,
            "daylight": self.daylight,
            "sunrise": self.sunrise,
            "sunset": self.sunset,
        }

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "DayNightCycle":

        cycle = cls()

        cycle.sol_length = data.get(
            "sol_length",
            cycle.sol_length,
        )

        cycle.minute = data.get(
            "minute",
            0,
        )
        cycle.fractional_minute = data.get("fractional_minute", 0.0)

        cycle.sunlight = data.get(
            "sunlight",
            1.0,
        )

        cycle.solar_efficiency = data.get(
            "solar_efficiency",
            1.0,
        )

        cycle.temperature_modifier = data.get(
            "temperature_modifier",
            0.0,
        )

        cycle.daylight = data.get(
            "daylight",
            True,
        )

        cycle.sunrise = data.get(
            "sunrise",
            360,
        )

        cycle.sunset = data.get(
            "sunset",
            1080,
        )

        return cycle

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "DayNightCycle("
            f"time={self.hour:.2f}h, "
            f"daylight={self.daylight}, "
            f"sunlight={self.sunlight:.2f}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

SolCycle = DayNightCycle
