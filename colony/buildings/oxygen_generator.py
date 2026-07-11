"""
oxygen_generator.py

Part 1/5

Canonical Oxygen Generator.

Produces breathable oxygen for the colony.

Consumes

- Power

Produces

- Oxygen
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.oxygen import Oxygen
from colony.resources.power import Power

# ============================================================
# Oxygen Generator
# ============================================================


@dataclass
class OxygenGenerator(BaseBuilding):

    name: str = "Oxygen Generator"

    description: str = "Electrolysis system producing breathable oxygen."

    building_id: int = 0

    position: tuple[int, int] = (0, 0)

    level: int = 1

    power_required: float = 8.0

    oxygen_output: float = 25.0

    oxygen: Oxygen = field(
        default_factory=Oxygen,
    )

    power: Power = field(
        default_factory=Power,
    )

    total_oxygen_generated: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.generate_oxygen()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        # ========================================================

    # Production
    # ========================================================

    def generate_oxygen(
        self,
    ) -> float:

        if not self.operational or self.power.current_amount < self.power_required:

            return 0.0

        self.power.consume(
            self.power_required,
        )

        generated = self.oxygen_output * self.efficiency

        produced = self.oxygen.generate(
            generated,
        )

        self.total_oxygen_generated += produced

        return produced

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_output(
        self,
    ) -> float:

        return self.oxygen_output * self.efficiency

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_consumption <= 0:

            return 0.0

        return self.effective_output / self.power_required

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "integrity": round(
                    self.integrity,
                    2,
                ),
                "efficiency": round(
                    self.efficiency,
                    2,
                ),
                "operational": self.operational,
                "oxygen_output": round(
                    self.oxygen_output,
                    2,
                ),
                "effective_output": round(
                    self.effective_output,
                    2,
                ),
                "power_consumption": round(
                    self.power_consumption,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "total_oxygen_generated": round(
                    self.total_oxygen_generated,
                    2,
                ),
                "oxygen": self.oxygen.statistics(),
                "power": self.power.statistics(),
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "OxygenGenerator("
            f"integrity={self.integrity:.1f}%, "
            f"efficiency={self.efficiency:.2f}, "
            f"output={self.effective_output:.2f} O₂/h, "
            f"power={self.power_consumption:.2f} kWh"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

O2Generator = OxygenGenerator
