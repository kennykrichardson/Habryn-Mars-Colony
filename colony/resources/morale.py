"""
morale.py

Part 1/4

Canonical Morale resource.

Represents the overall psychological wellbeing
of the colony population.

Used by

- Habitats
- Recreation Facilities
- Medical Bays
- AI Management
"""

from __future__ import annotations

from dataclasses import dataclass

from colony.resources.base_resource import BaseResource

# ============================================================
# Morale
# ============================================================


@dataclass
class Morale(BaseResource):

    name: str = "Morale"

    unit: str = "%"

    storage_capacity: float = 100.0

    current_amount: float = 80.0

    recovery_rate: float = 0.0

    decay_rate: float = 0.0

    recreation_bonus: float = 1.0

    leadership_bonus: float = 1.0

    stress_multiplier: float = 1.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        self.recover(
            self.recovery_rate * self.recreation_bonus * self.leadership_bonus,
        )

        self.consume(
            self.decay_rate * self.stress_multiplier,
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
    # Morale Operations
    # ========================================================

    def recover(
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

    def boost(
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

        return self.boost(
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

        return self.current_amount <= 25.0

    @property
    def storage_percentage(
        self,
    ) -> float:

        if self.storage_capacity <= 0:

            return 0.0

        return (self.current_amount / self.storage_capacity) * 100.0

    @property
    def effective_recovery_rate(
        self,
    ) -> float:

        return self.recovery_rate * self.recreation_bonus * self.leadership_bonus

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "recovery_rate": round(
                    self.recovery_rate,
                    2,
                ),
                "decay_rate": round(
                    self.decay_rate,
                    2,
                ),
                "recreation_bonus": round(
                    self.recreation_bonus,
                    2,
                ),
                "leadership_bonus": round(
                    self.leadership_bonus,
                    2,
                ),
                "stress_multiplier": round(
                    self.stress_multiplier,
                    2,
                ),
                "effective_recovery_rate": round(
                    self.effective_recovery_rate,
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
                "recovery_rate": self.recovery_rate,
                "decay_rate": self.decay_rate,
                "recreation_bonus": self.recreation_bonus,
                "leadership_bonus": self.leadership_bonus,
                "stress_multiplier": self.stress_multiplier,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Morale":

        morale = cls()

        morale.current_amount = data.get(
            "current_amount",
            morale.current_amount,
        )

        morale.storage_capacity = data.get(
            "storage_capacity",
            morale.storage_capacity,
        )

        morale.recovery_rate = data.get(
            "recovery_rate",
            morale.recovery_rate,
        )

        morale.decay_rate = data.get(
            "decay_rate",
            morale.decay_rate,
        )

        morale.recreation_bonus = data.get(
            "recreation_bonus",
            morale.recreation_bonus,
        )

        morale.leadership_bonus = data.get(
            "leadership_bonus",
            morale.leadership_bonus,
        )

        morale.stress_multiplier = data.get(
            "stress_multiplier",
            morale.stress_multiplier,
        )

        return morale

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Morale("
            f"{self.current_amount:.1f}/{self.storage_capacity:.1f}%, "
            f"recovery={self.effective_recovery_rate:.2f}, "
            f"stress={self.stress_multiplier:.2f}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

ColonyMorale = Morale
