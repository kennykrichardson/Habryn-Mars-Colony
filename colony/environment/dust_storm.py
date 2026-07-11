"""
dust_storm.py

Part 1/4

Canonical Dust Storm system.

Responsible for dust storm simulation.

Owns

- storm lifecycle
- storm intensity
- radius
- movement
- visibility penalties

WeatherSystem may create DustStorms.
This system simulates them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random

# ============================================================
# Storm State
# ============================================================


class StormState(Enum):

    FORMING = "Forming"

    ACTIVE = "Active"

    DISSIPATING = "Dissipating"

    ENDED = "Ended"


# ============================================================
# Dust Storm
# ============================================================


@dataclass
class DustStorm:

    center: tuple[float, float] = (0.0, 0.0)

    radius: float = 10.0

    intensity: float = 0.0

    movement_speed: float = 0.5

    direction: tuple[int, int] = (1, 0)

    duration: int = 0

    max_duration: int = 240

    state: StormState = StormState.FORMING

    active: bool = False

    # ========================================================
    # Lifecycle
    # ========================================================

    def start(
        self,
    ) -> None:

        self.active = True

        self.state = StormState.ACTIVE

        self.intensity = 0.25

    def stop(
        self,
    ) -> None:

        self.active = False

        self.state = StormState.ENDED

    def randomize(
        self,
    ) -> None:

        self.center = (
            random.uniform(0.0, 100.0),
            random.uniform(0.0, 100.0),
        )

        self.radius = random.uniform(
            5.0,
            40.0,
        )

        self.intensity = random.uniform(
            0.2,
            1.0,
        )

        self.direction = random.choice(
            [
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
                (-1, -1),
                (1, 1),
                (-1, 1),
                (1, -1),
            ]
        )

        # ========================================================

    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        if not self.active:

            return

        self.duration += 1

        x, y = self.center

        dx, dy = self.direction

        self.center = (
            x + (dx * self.movement_speed),
            y + (dy * self.movement_speed),
        )

        if self.duration >= self.max_duration:

            self.state = StormState.DISSIPATING

        if self.state == StormState.DISSIPATING:

            self.intensity = max(
                0.0,
                self.intensity - 0.01,
            )

            if self.intensity <= 0:

                self.stop()

    def hourly_update(
        self,
    ) -> None:

        self.step()

    def daily_update(
        self,
    ) -> None:

        pass

    # ========================================================
    # Queries
    # ========================================================

    def contains(
        self,
        position: tuple[int, int],
    ) -> bool:

        x, y = position

        cx, cy = self.center

        return ((x - cx) ** 2 + (y - cy) ** 2) <= self.radius**2

    @property
    def visibility_modifier(
        self,
    ) -> float:

        return max(
            0.1,
            1.0 - self.intensity,
        )

    @property
    def movement_modifier(
        self,
    ) -> float:

        return max(
            0.2,
            1.0 - (self.intensity * 0.8),
        )

    @property
    def communication_modifier(
        self,
    ) -> float:

        return max(
            0.25,
            1.0 - (self.intensity * 0.7),
        )

        # ========================================================

    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        return {
            "active": self.active,
            "state": self.state.value,
            "center": self.center,
            "radius": round(
                self.radius,
                2,
            ),
            "intensity": round(
                self.intensity,
                2,
            ),
            "movement_speed": round(
                self.movement_speed,
                2,
            ),
            "direction": self.direction,
            "duration": self.duration,
            "max_duration": self.max_duration,
            "visibility_modifier": round(
                self.visibility_modifier,
                2,
            ),
            "movement_modifier": round(
                self.movement_modifier,
                2,
            ),
            "communication_modifier": round(
                self.communication_modifier,
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
            "center": self.center,
            "radius": self.radius,
            "intensity": self.intensity,
            "movement_speed": self.movement_speed,
            "direction": self.direction,
            "duration": self.duration,
            "max_duration": self.max_duration,
            "state": self.state.value,
            "active": self.active,
        }

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "DustStorm":

        storm = cls()

        center_x, center_y = data.get(
            "center",
            (0.0, 0.0),
        )

        storm.center = (
            float(center_x),
            float(center_y),
        )

        storm.radius = float(
            data.get(
                "radius",
                10.0,
            )
        )

        storm.intensity = float(
            data.get(
                "intensity",
                0.0,
            )
        )

        storm.movement_speed = float(
            data.get(
                "movement_speed",
                0.5,
            )
        )

        direction_x, direction_y = data.get(
            "direction",
            (1, 0),
        )

        storm.direction = (
            int(direction_x),
            int(direction_y),
        )

        storm.duration = int(
            data.get(
                "duration",
                0,
            )
        )

        storm.max_duration = int(
            data.get(
                "max_duration",
                240,
            )
        )

        storm.state = StormState(
            data.get(
                "state",
                StormState.FORMING.value,
            )
        )

        storm.active = bool(
            data.get(
                "active",
                False,
            )
        )

        return storm

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "DustStorm("
            f"state='{self.state.value}', "
            f"center={self.center}, "
            f"radius={self.radius:.1f}, "
            f"intensity={self.intensity:.2f}"
            ")"
        )
