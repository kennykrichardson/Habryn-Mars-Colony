"""
water.py

Part 1/4

Canonical Water resource.

Represents all usable water in the colony.

Used by

- Habitats
- Greenhouses
- Water Plants
- Life Support
- Agriculture
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Water
# ============================================================


@dataclass
class Water(BaseResource):

    name: str = "Water"

    unit: str = "L"

    storage_capacity: float = 500000.0

    current_amount: float = 350000.0

    purity: float = 99.5

    temperature: float = 5.0

    leakage_rate: float = 0.0

    emergency_reserve: float = 25000.0

    generation_rate: float = 0.0

    consumption_rate: float = 0.0

    recycling_rate: float = 0.0

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

        self.recycle(
            self.recycling_rate,
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
    # Water Operations
    # ========================================================

    def generate(
        self,
        amount: float,
    ) -> float:

        return self.add(
            amount,
        )

    def recycle(
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
    def purity_percentage(
        self,
    ) -> float:

        return self.purity

    @property
    def storage_percentage(
        self,
    ) -> float:

        if self.storage_capacity <= 0:

            return 0.0

        return (self.current_amount / self.storage_capacity) * 100.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "purity": round(
                    self.purity,
                    2,
                ),
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
                "recycling_rate": round(
                    self.recycling_rate,
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
                "purity": self.purity,
                "temperature": self.temperature,
                "leakage_rate": self.leakage_rate,
                "emergency_reserve": self.emergency_reserve,
                "generation_rate": self.generation_rate,
                "consumption_rate": self.consumption_rate,
                "recycling_rate": self.recycling_rate,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Water":

        water = cls()

        water.current_amount = data.get(
            "current_amount",
            water.current_amount,
        )

        water.storage_capacity = data.get(
            "storage_capacity",
            water.storage_capacity,
        )

        water.purity = data.get(
            "purity",
            water.purity,
        )

        water.temperature = data.get(
            "temperature",
            water.temperature,
        )

        water.leakage_rate = data.get(
            "leakage_rate",
            water.leakage_rate,
        )

        water.emergency_reserve = data.get(
            "emergency_reserve",
            water.emergency_reserve,
        )

        water.generation_rate = data.get(
            "generation_rate",
            water.generation_rate,
        )

        water.consumption_rate = data.get(
            "consumption_rate",
            water.consumption_rate,
        )

        water.recycling_rate = data.get(
            "recycling_rate",
            water.recycling_rate,
        )

        return water

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Water("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f} L, "
            f"{self.storage_percentage:.1f}%, "
            f"purity={self.purity:.2f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

H2O = Water
