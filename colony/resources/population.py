"""
population.py

Part 1/4

Canonical Population resource.

Represents the colony population capacity and
available workforce.

Used by

- Habitats
- Medical Bays
- AI Manager
- Colony Model
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Population
# ============================================================


@dataclass
class Population(BaseResource):

    name: str = "Population"

    unit: str = "People"

    storage_capacity: float = 1000.0

    current_amount: float = 20.0

    birth_rate: float = 0.0

    death_rate: float = 0.0

    immigration_rate: float = 0.0

    emigration_rate: float = 0.0

    productivity_bonus: float = 1.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        self.add_population(
            self.birth_rate,
        )

        self.add_population(
            self.immigration_rate,
        )

        self.remove_population(
            self.death_rate,
        )

        self.remove_population(
            self.emigration_rate,
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
    # Population Operations
    # ========================================================

    def add_population(
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

    def remove_population(
        self,
        amount: float,
    ) -> float:

        return super().consume(
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

        return self.current_amount <= 5.0

    @property
    def storage_percentage(
        self,
    ) -> float:

        if self.storage_capacity <= 0:

            return 0.0

        return (self.current_amount / self.storage_capacity) * 100.0

    @property
    def workforce(
        self,
    ) -> float:

        return self.current_amount * self.productivity_bonus

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "birth_rate": round(
                    self.birth_rate,
                    2,
                ),
                "death_rate": round(
                    self.death_rate,
                    2,
                ),
                "immigration_rate": round(
                    self.immigration_rate,
                    2,
                ),
                "emigration_rate": round(
                    self.emigration_rate,
                    2,
                ),
                "productivity_bonus": round(
                    self.productivity_bonus,
                    2,
                ),
                "workforce": round(
                    self.workforce,
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
                "birth_rate": self.birth_rate,
                "death_rate": self.death_rate,
                "immigration_rate": self.immigration_rate,
                "emigration_rate": self.emigration_rate,
                "productivity_bonus": self.productivity_bonus,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Population":

        population = cls()

        population.current_amount = data.get(
            "current_amount",
            population.current_amount,
        )

        population.storage_capacity = data.get(
            "storage_capacity",
            population.storage_capacity,
        )

        population.birth_rate = data.get(
            "birth_rate",
            population.birth_rate,
        )

        population.death_rate = data.get(
            "death_rate",
            population.death_rate,
        )

        population.immigration_rate = data.get(
            "immigration_rate",
            population.immigration_rate,
        )

        population.emigration_rate = data.get(
            "emigration_rate",
            population.emigration_rate,
        )

        population.productivity_bonus = data.get(
            "productivity_bonus",
            population.productivity_bonus,
        )

        return population

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Population("
            f"{self.current_amount:.0f}/{self.storage_capacity:.0f} people, "
            f"{self.storage_percentage:.1f}%, "
            f"workforce={self.workforce:.1f}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Colonists = Population
