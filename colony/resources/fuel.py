"""
fuel.py

Part 1/4

Canonical Fuel resource.

Represents every combustible or reactor fuel
used throughout the colony.

Used by

- Rovers
- Reactors
- Emergency Generators
- Construction Vehicles
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Fuel
# ============================================================


@dataclass
class Fuel(BaseResource):

    name: str = "Fuel"

    unit: str = "L"

    storage_capacity: float = 250000.0

    current_amount: float = 120000.0

    energy_density: float = 42.0

    quality: float = 98.0

    production_rate: float = 0.0

    consumption_rate: float = 0.0

    leakage_rate: float = 0.0

    emergency_reserve: float = 10000.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        self.produce(
            self.production_rate,
        )

        self.consume(
            self.consumption_rate,
        )

        self.lose(
            self.leakage_rate,
        )

    def hourly_update(
        self,
    ) -> None:

        self.step()

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

    # ========================================================
    # Fuel Operations
    # ========================================================

    def produce(
        self,
        amount: float,
    ) -> float:

        return self.add(
            amount,
        )

    def generate(
        self,
        amount: float,
    ) -> float:

        return self.produce(
            amount,
        )

    def consume(
        self,
        amount: float,
    ) -> float:

        return super().consume(
            amount,
        )

    def lose(
        self,
        amount: float,
    ) -> float:

        return super().lose(
            amount,
        )

    def refill(
        self,
    ) -> None:

        self.current_amount = self.storage_capacity

        # ========================================================

    # Queries
    # ========================================================

    @property
    def is_low(
        self,
    ) -> bool:

        return self.current_amount <= self.emergency_reserve

    @property
    def storage_percentage(
        self,
    ) -> float:

        if self.storage_capacity <= 0:

            return 0.0

        return (self.current_amount / self.storage_capacity) * 100.0

    @property
    def available_energy(
        self,
    ) -> float:

        return self.current_amount * self.energy_density

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "energy_density": round(
                    self.energy_density,
                    2,
                ),
                "quality": round(
                    self.quality,
                    2,
                ),
                "production_rate": round(
                    self.production_rate,
                    2,
                ),
                "consumption_rate": round(
                    self.consumption_rate,
                    2,
                ),
                "leakage_rate": round(
                    self.leakage_rate,
                    2,
                ),
                "emergency_reserve": round(
                    self.emergency_reserve,
                    2,
                ),
                "available_energy": round(
                    self.available_energy,
                    2,
                ),
                "low": self.is_low,
            }
        )

        return stats

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data.update(
            {
                "energy_density": self.energy_density,
                "quality": self.quality,
                "production_rate": self.production_rate,
                "consumption_rate": self.consumption_rate,
                "leakage_rate": self.leakage_rate,
                "emergency_reserve": self.emergency_reserve,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Fuel":

        fuel = cls()

        fuel.current_amount = data.get(
            "current_amount",
            fuel.current_amount,
        )

        fuel.storage_capacity = data.get(
            "storage_capacity",
            fuel.storage_capacity,
        )

        fuel.energy_density = data.get(
            "energy_density",
            fuel.energy_density,
        )

        fuel.quality = data.get(
            "quality",
            fuel.quality,
        )

        fuel.production_rate = data.get(
            "production_rate",
            fuel.production_rate,
        )

        fuel.consumption_rate = data.get(
            "consumption_rate",
            fuel.consumption_rate,
        )

        fuel.leakage_rate = data.get(
            "leakage_rate",
            fuel.leakage_rate,
        )

        fuel.emergency_reserve = data.get(
            "emergency_reserve",
            fuel.emergency_reserve,
        )

        return fuel

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Fuel("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f} L, "
            f"{self.storage_percentage:.1f}%, "
            f"quality={self.quality:.1f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Propellant = Fuel
