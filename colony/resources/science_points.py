"""
science_points.py

Part 1/4

Canonical Science Points resource.

Represents accumulated research points available
for unlocking colony technologies.

Used by

- Laboratories
- Scientists
- Research Manager
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Science Points
# ============================================================


@dataclass
class SciencePoints(BaseResource):

    name: str = "Science Points"

    unit: str = "SP"

    storage_capacity: float = 100000.0

    current_amount: float = 0.0

    generation_rate: float = 0.0

    consumption_rate: float = 0.0

    research_bonus: float = 1.0

    collaboration_bonus: float = 1.0

    discovery_multiplier: float = 1.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        self.generate(
            self.generation_rate * self.discovery_multiplier,
        )

        self.consume(
            self.consumption_rate,
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
    # Science Operations
    # ========================================================

    def generate(
        self,
        amount: float,
    ) -> float:

        return self.add(
            amount,
        )

    def spend(
        self,
        amount: float,
    ) -> float:

        return super().consume(
            amount,
        )

    def consume(
        self,
        amount: float,
    ) -> float:

        return self.spend(
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

        return self.current_amount <= 0.0

    @property
    def storage_percentage(
        self,
    ) -> float:

        if self.storage_capacity <= 0:

            return 0.0

        return (self.current_amount / self.storage_capacity) * 100.0

    @property
    def effective_generation_rate(
        self,
    ) -> float:

        return (
            self.generation_rate
            * self.research_bonus
            * self.collaboration_bonus
            * self.discovery_multiplier
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
                "generation_rate": round(
                    self.generation_rate,
                    2,
                ),
                "consumption_rate": round(
                    self.consumption_rate,
                    2,
                ),
                "research_bonus": round(
                    self.research_bonus,
                    2,
                ),
                "collaboration_bonus": round(
                    self.collaboration_bonus,
                    2,
                ),
                "discovery_multiplier": round(
                    self.discovery_multiplier,
                    2,
                ),
                "effective_generation_rate": round(
                    self.effective_generation_rate,
                    2,
                ),
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
                "generation_rate": self.generation_rate,
                "consumption_rate": self.consumption_rate,
                "research_bonus": self.research_bonus,
                "collaboration_bonus": self.collaboration_bonus,
                "discovery_multiplier": self.discovery_multiplier,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "SciencePoints":

        science = cls()

        science.current_amount = data.get(
            "current_amount",
            science.current_amount,
        )

        science.storage_capacity = data.get(
            "storage_capacity",
            science.storage_capacity,
        )

        science.generation_rate = data.get(
            "generation_rate",
            science.generation_rate,
        )

        science.consumption_rate = data.get(
            "consumption_rate",
            science.consumption_rate,
        )

        science.research_bonus = data.get(
            "research_bonus",
            science.research_bonus,
        )

        science.collaboration_bonus = data.get(
            "collaboration_bonus",
            science.collaboration_bonus,
        )

        science.discovery_multiplier = data.get(
            "discovery_multiplier",
            science.discovery_multiplier,
        )

        return science

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "SciencePoints("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f} SP, "
            f"{self.storage_percentage:.1f}%, "
            f"bonus={self.research_bonus:.2f}x"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

ResearchPoints = SciencePoints
