"""
weather.py

Part 1/4

Canonical Martian weather simulation.

Owns

- current weather
- temperature
- wind
- pressure
- visibility

Dust storms are implemented separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random

# ============================================================
# Weather Types
# ============================================================


class WeatherType(Enum):

    CLEAR = "Clear"

    CLOUDY = "Cloudy"

    WINDY = "Windy"

    DUSTY = "Dusty"

    DUST_STORM = "Dust Storm"

    COLD_FRONT = "Cold Front"


# ============================================================
# Weather System
# ============================================================


@dataclass
class WeatherSystem:

    weather: WeatherType = WeatherType.CLEAR

    temperature: float = -45.0

    wind_speed: float = 5.0

    pressure: float = 610.0

    visibility: float = 100.0

    humidity: float = 0.01

    radiation_modifier: float = 1.0

    dust_storm_frequency: float = 1.0

    # ========================================================
    # Weather Generation
    # ========================================================

    def randomize(
        self,
    ) -> None:

        choices = list(WeatherType)
        weights = [self.dust_storm_frequency if item == WeatherType.DUST_STORM else 1.0
                   for item in choices]
        self.weather = random.choices(choices, weights=weights, k=1)[0]

        self.temperature = random.uniform(
            -120.0,
            20.0,
        )

        self.wind_speed = random.uniform(
            0.0,
            40.0,
        )

        self.pressure = random.uniform(
            500.0,
            900.0,
        )

        self.visibility = random.uniform(
            10.0,
            100.0,
        )

        self.humidity = random.uniform(
            0.0,
            0.05,
        )

        self._update_modifiers()

    # ========================================================
    # Modifiers
    # ========================================================

    def _update_modifiers(
        self,
    ) -> None:

        if self.weather == WeatherType.CLEAR:

            self.radiation_modifier = 1.2

        elif self.weather == WeatherType.CLOUDY:

            self.radiation_modifier = 1.0

        elif self.weather == WeatherType.WINDY:

            self.radiation_modifier = 0.95

        elif self.weather == WeatherType.DUSTY:

            self.radiation_modifier = 0.75

        elif self.weather == WeatherType.DUST_STORM:

            self.radiation_modifier = 0.50

        else:

            self.radiation_modifier = 0.90

        # ========================================================

    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        self.randomize()

    def hourly_update(
        self,
    ) -> None:

        self.randomize()

    def daily_update(
        self,
    ) -> None:

        self.randomize()

    # ========================================================
    # Queries
    # ========================================================

    @property
    def is_clear(
        self,
    ) -> bool:

        return self.weather == WeatherType.CLEAR

    @property
    def is_storm(
        self,
    ) -> bool:

        return self.weather == WeatherType.DUST_STORM

    @property
    def movement_modifier(
        self,
    ) -> float:

        if self.weather == WeatherType.CLEAR:

            return 1.0

        if self.weather == WeatherType.CLOUDY:

            return 0.95

        if self.weather == WeatherType.WINDY:

            return 0.85

        if self.weather == WeatherType.DUSTY:

            return 0.70

        if self.weather == WeatherType.DUST_STORM:

            return 0.30

        return 0.80

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        return {
            "weather": self.weather.value,
            "temperature": round(
                self.temperature,
                2,
            ),
            "wind_speed": round(
                self.wind_speed,
                2,
            ),
            "pressure": round(
                self.pressure,
                2,
            ),
            "visibility": round(
                self.visibility,
                2,
            ),
            "humidity": round(
                self.humidity,
                4,
            ),
            "radiation_modifier": round(
                self.radiation_modifier,
                2,
            ),
            "dust_storm_frequency": self.dust_storm_frequency,
            "movement_modifier": round(
                self.movement_modifier,
                2,
            ),
        }

        # ========================================================

    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        return {
            "weather": self.weather.value,
            "temperature": self.temperature,
            "wind_speed": self.wind_speed,
            "pressure": self.pressure,
            "visibility": self.visibility,
            "humidity": self.humidity,
            "radiation_modifier": self.radiation_modifier,
            "dust_storm_frequency": self.dust_storm_frequency,
        }

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "WeatherSystem":

        system = cls()

        system.weather = WeatherType(
            data.get(
                "weather",
                WeatherType.CLEAR.value,
            )
        )

        system.temperature = data.get(
            "temperature",
            -45.0,
        )

        system.wind_speed = data.get(
            "wind_speed",
            5.0,
        )

        system.pressure = data.get(
            "pressure",
            610.0,
        )

        system.visibility = data.get(
            "visibility",
            100.0,
        )

        system.humidity = data.get(
            "humidity",
            0.01,
        )

        system.radiation_modifier = data.get(
            "radiation_modifier",
            1.0,
        )
        system.dust_storm_frequency = data.get("dust_storm_frequency", 1.0)

        return system

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "WeatherSystem("
            f"weather='{self.weather.value}', "
            f"temp={self.temperature:.1f}°C, "
            f"wind={self.wind_speed:.1f}m/s"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Weather = WeatherSystem
