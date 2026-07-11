"""
food.py

Part 1/4

Canonical Food resource.

Represents edible food available to the colony.

Used by

- Habitats
- Colonists
- Greenhouses
- Storage Facilities
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Food
# ============================================================


@dataclass
class Food(BaseResource):

    name: str = "Food"

    unit: str = "kg"

    storage_capacity: float = 250000.0

    current_amount: float = 150000.0

    freshness: float = 100.0

    spoilage_rate: float = 0.02

    nutrition_quality: float = 100.0

    emergency_reserve: float = 10000.0

    production_rate: float = 0.0

    consumption_rate: float = 0.0

    waste_rate: float = 0.0

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

        self.spoil()

        self.discard(
            self.waste_rate,
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
    # Food Operations
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

    def discard(
        self,
        amount: float,
    ) -> float:

        return super().lose(
            amount,
        )

    def spoil(
        self,
    ) -> None:

        self.freshness = max(
            0.0,
            self.freshness - self.spoilage_rate,
        )

    def refill(
        self,
    ) -> None:

        self.current_amount = self.storage_capacity

        self.freshness = 100.0

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
    def edible(
        self,
    ) -> bool:

        return self.freshness > 20.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "freshness": round(
                    self.freshness,
                    2,
                ),
                "nutrition_quality": round(
                    self.nutrition_quality,
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
                "spoilage_rate": round(
                    self.spoilage_rate,
                    4,
                ),
                "waste_rate": round(
                    self.waste_rate,
                    2,
                ),
                "emergency_reserve": round(
                    self.emergency_reserve,
                    2,
                ),
                "edible": self.edible,
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
                "freshness": self.freshness,
                "nutrition_quality": self.nutrition_quality,
                "spoilage_rate": self.spoilage_rate,
                "production_rate": self.production_rate,
                "consumption_rate": self.consumption_rate,
                "waste_rate": self.waste_rate,
                "emergency_reserve": self.emergency_reserve,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Food":

        food = cls()

        food.current_amount = data.get(
            "current_amount",
            food.current_amount,
        )

        food.storage_capacity = data.get(
            "storage_capacity",
            food.storage_capacity,
        )

        food.freshness = data.get(
            "freshness",
            food.freshness,
        )

        food.spoilage_rate = data.get(
            "spoilage_rate",
            food.spoilage_rate,
        )

        food.nutrition_quality = data.get(
            "nutrition_quality",
            food.nutrition_quality,
        )

        food.production_rate = data.get(
            "production_rate",
            food.production_rate,
        )

        food.consumption_rate = data.get(
            "consumption_rate",
            food.consumption_rate,
        )

        food.waste_rate = data.get(
            "waste_rate",
            food.waste_rate,
        )

        food.emergency_reserve = data.get(
            "emergency_reserve",
            food.emergency_reserve,
        )

        return food

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Food("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f} kg, "
            f"{self.storage_percentage:.1f}%, "
            f"freshness={self.freshness:.1f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Rations = Food
