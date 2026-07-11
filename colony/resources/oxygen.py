"""
oxygen.py

Part 1/4

Canonical Oxygen resource.

Represents breathable oxygen available to the colony.

Used by

- Habitats
- EVA
- Life Support
- Oxygen Generators
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Oxygen
# ============================================================


@dataclass
class Oxygen(BaseResource):

    name: str = "Oxygen"

    unit: str = "kg"

    storage_capacity: float = 100000.0

    current_amount: float = 80000.0

    purity: float = 99.8

    pressure: float = 101.3

    leakage_rate: float = 0.0

    emergency_reserve: float = 5000.0

    generation_rate: float = 0.0

    consumption_rate: float = 0.0

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
    # Oxygen Operations
    # ========================================================

    def generate(
        self,
        amount: float,
    ) -> float:

        return super().add(
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
                "pressure": round(
                    self.pressure,
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
                "pressure": self.pressure,
                "leakage_rate": self.leakage_rate,
                "emergency_reserve": self.emergency_reserve,
                "generation_rate": self.generation_rate,
                "consumption_rate": self.consumption_rate,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Oxygen":

        oxygen = cls()

        oxygen.current_amount = data.get(
            "current_amount",
            oxygen.current_amount,
        )

        oxygen.storage_capacity = data.get(
            "storage_capacity",
            oxygen.storage_capacity,
        )

        oxygen.purity = data.get(
            "purity",
            oxygen.purity,
        )

        oxygen.pressure = data.get(
            "pressure",
            oxygen.pressure,
        )

        oxygen.leakage_rate = data.get(
            "leakage_rate",
            oxygen.leakage_rate,
        )

        oxygen.emergency_reserve = data.get(
            "emergency_reserve",
            oxygen.emergency_reserve,
        )

        oxygen.generation_rate = data.get(
            "generation_rate",
            oxygen.generation_rate,
        )

        oxygen.consumption_rate = data.get(
            "consumption_rate",
            oxygen.consumption_rate,
        )

        return oxygen

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Oxygen("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f} kg, "
            f"{self.storage_percentage:.1f}%, "
            f"purity={self.purity:.2f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

O2 = Oxygen
