"""
waste.py

Part 1/4

Canonical Waste resource.

Represents accumulated waste products within
the colony.

Used by

- Habitats
- Recycling Plants
- Water Plants
- Waste Processing Facilities
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Waste
# ============================================================


@dataclass
class Waste(BaseResource):

    name: str = "Waste"

    unit: str = "kg"

    storage_capacity: float = 300000.0

    current_amount: float = 10000.0

    toxicity: float = 5.0

    contamination: float = 0.0

    production_rate: float = 0.0

    recycling_rate: float = 0.0

    disposal_rate: float = 0.0

    emergency_limit: float = 250000.0

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

        self.recycle(
            self.recycling_rate,
        )

        self.dispose(
            self.disposal_rate,
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
    # Waste Operations
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

    def recycle(
        self,
        amount: float,
    ) -> float:

        return super().consume(
            amount,
        )

    def dispose(
        self,
        amount: float,
    ) -> float:

        return super().lose(
            amount,
        )

    def empty(
        self,
    ) -> None:

        self.current_amount = 0.0

    # ========================================================
    # Queries
    # ========================================================

    @property
    def is_full(
        self,
    ) -> bool:

        return self.current_amount >= self.emergency_limit

    @property
    def fill_percentage(
        self,
    ) -> float:

        if self.storage_capacity <= 0:

            return 0.0

        return (self.current_amount / self.storage_capacity) * 100.0

    @property
    def safe_capacity(
        self,
    ) -> float:

        return max(
            0.0,
            self.emergency_limit - self.current_amount,
        )

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "toxicity": round(
                    self.toxicity,
                    2,
                ),
                "contamination": round(
                    self.contamination,
                    2,
                ),
                "production_rate": round(
                    self.production_rate,
                    2,
                ),
                "recycling_rate": round(
                    self.recycling_rate,
                    2,
                ),
                "disposal_rate": round(
                    self.disposal_rate,
                    2,
                ),
                "emergency_limit": round(
                    self.emergency_limit,
                    2,
                ),
                "safe_capacity": round(
                    self.safe_capacity,
                    2,
                ),
                "full": self.is_full,
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
                "toxicity": self.toxicity,
                "contamination": self.contamination,
                "production_rate": self.production_rate,
                "recycling_rate": self.recycling_rate,
                "disposal_rate": self.disposal_rate,
                "emergency_limit": self.emergency_limit,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Waste":

        waste = cls()

        waste.current_amount = data.get(
            "current_amount",
            waste.current_amount,
        )

        waste.storage_capacity = data.get(
            "storage_capacity",
            waste.storage_capacity,
        )

        waste.toxicity = data.get(
            "toxicity",
            waste.toxicity,
        )

        waste.contamination = data.get(
            "contamination",
            waste.contamination,
        )

        waste.production_rate = data.get(
            "production_rate",
            waste.production_rate,
        )

        waste.recycling_rate = data.get(
            "recycling_rate",
            waste.recycling_rate,
        )

        waste.disposal_rate = data.get(
            "disposal_rate",
            waste.disposal_rate,
        )

        waste.emergency_limit = data.get(
            "emergency_limit",
            waste.emergency_limit,
        )

        return waste

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Waste("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f} kg, "
            f"{self.fill_percentage:.1f}%, "
            f"toxicity={self.toxicity:.1f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Refuse = Waste
