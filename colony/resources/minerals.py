"""
minerals.py

Part 1/4

Canonical Minerals resource.

Represents all mined raw materials used for
construction, manufacturing and research.

Used by

- Mines
- Workshops
- Construction
- Laboratories
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Minerals
# ============================================================


@dataclass
class Minerals(BaseResource):

    name: str = "Minerals"

    unit: str = "kg"

    storage_capacity: float = 1000000.0

    current_amount: float = 50000.0

    purity: float = 92.0

    extraction_rate: float = 0.0

    processing_rate: float = 0.0

    consumption_rate: float = 0.0

    waste_rate: float = 0.0

    emergency_reserve: float = 5000.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        self.extract(
            self.extraction_rate,
        )

        self.process(
            self.processing_rate,
        )

        self.consume(
            self.consumption_rate,
        )

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
    # Mineral Operations
    # ========================================================

    def extract(
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

    def process(
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

    def discard(
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
    def usable_minerals(
        self,
    ) -> float:

        return self.current_amount * (self.purity / 100.0)

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
                "extraction_rate": round(
                    self.extraction_rate,
                    2,
                ),
                "processing_rate": round(
                    self.processing_rate,
                    2,
                ),
                "consumption_rate": round(
                    self.consumption_rate,
                    2,
                ),
                "waste_rate": round(
                    self.waste_rate,
                    2,
                ),
                "emergency_reserve": round(
                    self.emergency_reserve,
                    2,
                ),
                "usable_minerals": round(
                    self.usable_minerals,
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
                "extraction_rate": self.extraction_rate,
                "processing_rate": self.processing_rate,
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
    ) -> "Minerals":

        minerals = cls()

        minerals.current_amount = data.get(
            "current_amount",
            minerals.current_amount,
        )

        minerals.storage_capacity = data.get(
            "storage_capacity",
            minerals.storage_capacity,
        )

        minerals.purity = data.get(
            "purity",
            minerals.purity,
        )

        minerals.extraction_rate = data.get(
            "extraction_rate",
            minerals.extraction_rate,
        )

        minerals.processing_rate = data.get(
            "processing_rate",
            minerals.processing_rate,
        )

        minerals.consumption_rate = data.get(
            "consumption_rate",
            minerals.consumption_rate,
        )

        minerals.waste_rate = data.get(
            "waste_rate",
            minerals.waste_rate,
        )

        minerals.emergency_reserve = data.get(
            "emergency_reserve",
            minerals.emergency_reserve,
        )

        return minerals

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Minerals("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f} kg, "
            f"{self.storage_percentage:.1f}%, "
            f"purity={self.purity:.1f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Ore = Minerals
