"""
solar_array.py

Part 1/5

Canonical Solar Array.

Primary renewable power source
for the colony.

Consumes

- Sunlight

Produces

- Power
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power

# ============================================================
# Solar Array
# ============================================================


@dataclass
class SolarArray(BaseBuilding):

    building_id: int = 0

    name: str = "Solar Array"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Large photovoltaic array supplying renewable energy."

    power_output: float = 60.0

    sunlight_efficiency: float = 1.0

    dust_penalty: float = 0.0

    tracking_bonus: float = 1.0

    power: Power = field(
        default_factory=Power,
    )

    total_power_generated: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.generate_power()

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

    def generate_power(
        self,
    ) -> float:

        if not self.operational:

            return 0.0

        generated = (
            self.power_output
            * self.efficiency
            * self.sunlight_efficiency
            * self.tracking_bonus
            * (1.0 - self.dust_penalty)
        )

        produced = self.power.generate(
            generated,
        )

        self.total_power_generated += produced

        return produced

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_output(
        self,
    ) -> float:

        return (
            self.power_output
            * self.efficiency
            * self.sunlight_efficiency
            * self.tracking_bonus
            * (1.0 - self.dust_penalty)
        )

    @property
    def panel_efficiency(
        self,
    ) -> float:

        return (
            self.efficiency
            * self.sunlight_efficiency
            * self.tracking_bonus
            * (1.0 - self.dust_penalty)
        )

    @property
    def requires_cleaning(
        self,
    ) -> bool:

        return self.dust_penalty >= 0.40

    def clean_panels(
        self,
        amount: float = 0.10,
    ) -> None:

        self.dust_penalty = max(
            0.0,
            self.dust_penalty - amount,
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
                "power_output": round(
                    self.power_output,
                    2,
                ),
                "effective_output": round(
                    self.effective_output,
                    2,
                ),
                "panel_efficiency": round(
                    self.panel_efficiency,
                    2,
                ),
                "sunlight_efficiency": round(
                    self.sunlight_efficiency,
                    2,
                ),
                "tracking_bonus": round(
                    self.tracking_bonus,
                    2,
                ),
                "dust_penalty": round(
                    self.dust_penalty,
                    2,
                ),
                "requires_cleaning": self.requires_cleaning,
                "total_power_generated": round(
                    self.total_power_generated,
                    2,
                ),
                "power": self.power.statistics(),
            }
        )

        return stats

    # ========================================================
    # Maintenance
    # ========================================================

    def apply_dust(
        self,
        amount: float,
    ) -> None:

        self.dust_penalty = min(
            0.90,
            self.dust_penalty + amount,
        )

    def restore_tracking(
        self,
        amount: float = 0.05,
    ) -> None:

        self.tracking_bonus = min(
            1.25,
            self.tracking_bonus + amount,
        )

    def degrade_tracking(
        self,
        amount: float = 0.05,
    ) -> None:

        self.tracking_bonus = max(
            0.50,
            self.tracking_bonus - amount,
        )

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "SolarArray("
            f"health={self.health_percentage:.1f}%, "
            f"output={self.effective_output:.2f} kWh, "
            f"dust={self.dust_penalty:.2f}, "
            f"tracking={self.tracking_bonus:.2f}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

PhotovoltaicArray = SolarArray
