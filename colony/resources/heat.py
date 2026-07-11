"""
heat.py

Part 1/4

Canonical Heat resource.

Represents thermal energy throughout the colony.

Used by

- Habitats
- Reactors
- Greenhouses
- Water Plants
- Thermal Control Systems
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Heat
# ============================================================


@dataclass
class Heat(BaseResource):

    name: str = "Heat"

    unit: str = "MJ"

    storage_capacity: float = 400000.0

    current_amount: float = 250000.0

    temperature: float = 22.0

    heat_loss_rate: float = 0.0

    generation_rate: float = 0.0

    consumption_rate: float = 0.0

    emergency_reserve: float = 25000.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        self.generate(
            self.generation_rate,
        )

        self.consume(
            self.consumption_rate,
        )

        self.lose(
            self.heat_loss_rate,
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
    # Heat Operations
    # ========================================================

    def generate(
        self,
        amount: float,
    ) -> float:

        return self.add(
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
    def thermal_energy(
        self,
    ) -> float:

        return self.current_amount

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "temperature": round(
                    self.temperature,
                    2,
                ),
                "generation_rate": round(
                    self.generation_rate,
                    2,
                ),
                "consumption_rate": round(
                    self.consumption_rate,
                    2,
                ),
                "heat_loss_rate": round(
                    self.heat_loss_rate,
                    2,
                ),
                "emergency_reserve": round(
                    self.emergency_reserve,
                    2,
                ),
                "thermal_energy": round(
                    self.thermal_energy,
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
                "temperature": self.temperature,
                "generation_rate": self.generation_rate,
                "consumption_rate": self.consumption_rate,
                "heat_loss_rate": self.heat_loss_rate,
                "emergency_reserve": self.emergency_reserve,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Heat":

        heat = cls()

        heat.current_amount = data.get(
            "current_amount",
            heat.current_amount,
        )

        heat.storage_capacity = data.get(
            "storage_capacity",
            heat.storage_capacity,
        )

        heat.temperature = data.get(
            "temperature",
            heat.temperature,
        )

        heat.generation_rate = data.get(
            "generation_rate",
            heat.generation_rate,
        )

        heat.consumption_rate = data.get(
            "consumption_rate",
            heat.consumption_rate,
        )

        heat.heat_loss_rate = data.get(
            "heat_loss_rate",
            heat.heat_loss_rate,
        )

        heat.emergency_reserve = data.get(
            "emergency_reserve",
            heat.emergency_reserve,
        )

        return heat

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Heat("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f} MJ, "
            f"{self.storage_percentage:.1f}%, "
            f"{self.temperature:.1f}°C"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

ThermalEnergy = Heat
