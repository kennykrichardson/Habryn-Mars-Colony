"""
water_plant.py

Part 1/5

Canonical Water Plant.

Processes and produces clean water
for the colony.

Consumes

- Power

Produces

- Water
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.water import Water

# ============================================================
# Water Plant
# ============================================================


@dataclass
class WaterPlant(BaseBuilding):

    building_id: int = 0

    name: str = "Water Plant"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Purifies and recycles water for colony use."

    power_required: float = 10.0

    water_output: float = 40.0

    water: Water = field(
        default_factory=Water,
    )

    power: Power = field(
        default_factory=Power,
    )

    total_water_generated: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.generate_water()

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

    def generate_water(
        self,
    ) -> float:

        if not self.operational or self.power.current_amount < self.power_required:

            return 0.0

        self.power.consume(
            self.power_required,
        )

        generated = self.water_output * self.efficiency

        produced = self.water.generate(
            generated,
        )

        self.total_water_generated += produced

        return produced

        # ========================================================

    # Status
    # ========================================================

    @property
    def effective_output(
        self,
    ) -> float:

        return self.water_output * self.efficiency

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_output / self.power_required

    @property
    def production_ratio(
        self,
    ) -> float:

        if self.water_output <= 0:

            return 0.0

        return self.effective_output / self.water_output

        # ========================================================

    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "water_output": round(
                    self.water_output,
                    2,
                ),
                "effective_output": round(
                    self.effective_output,
                    2,
                ),
                "power_required": round(
                    self.power_required,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "production_ratio": round(
                    self.production_ratio,
                    2,
                ),
                "total_water_generated": round(
                    self.total_water_generated,
                    2,
                ),
                "water": self.water.statistics(),
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
            "WaterPlant("
            f"health={self.health_percentage:.1f}%, "
            f"efficiency={self.efficiency:.2f}, "
            f"output={self.effective_output:.2f} L/h, "
            f"power={self.power_required:.2f} kWh"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

WaterTreatmentPlant = WaterPlant
