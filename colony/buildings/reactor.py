"""
reactor.py

Part 1/5

Canonical Nuclear Reactor.

Primary high-output power source for
large colonies.

Consumes

- Nuclear Fuel

Produces

- Power
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.fuel import Fuel
from colony.resources.heat import Heat

# ============================================================
# Reactor
# ============================================================


@dataclass
class Reactor(BaseBuilding):

    building_id: int = 0

    name: str = "Nuclear Reactor"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = (
        "Compact modular fission reactor supplying continuous electrical power."
    )

    power_output: float = 350.0

    fuel_consumption: float = 1.5

    heat_generation: float = 45.0

    safety_rating: float = 1.0

    coolant_efficiency: float = 1.0

    fuel: Fuel | None = None

    power: Power = field(
        default_factory=Power,
    )

    heat: Heat = field(
        default_factory=Heat,
    )

    total_power_generated: float = 0.0

    total_fuel_consumed: float = 0.0

    # ========================================================
    # Power Production
    # ========================================================

    def generate_power(
        self,
    ) -> float:

        if (not self.operational or self.fuel is None
                or self.fuel.current_amount < self.fuel_consumption):

            return 0.0

        self.fuel.consume(
            self.fuel_consumption,
        )

        self.total_fuel_consumed += self.fuel_consumption

        generated = self.power_output * self.efficiency * self.coolant_efficiency

        produced = self.power.generate(
            generated,
        )

        self.total_power_generated += produced

        return produced

    # ========================================================
    # Heat Production
    # ========================================================

    def generate_heat(
        self,
    ) -> float:

        generated = self.heat_generation * self.efficiency

        return self.heat.generate(
            generated,
        )

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_output(
        self,
    ) -> float:

        return self.power_output * self.efficiency * self.coolant_efficiency

    @property
    def fuel_efficiency(
        self,
    ) -> float:

        if self.fuel_consumption <= 0:

            return 0.0

        return self.effective_output / self.fuel_consumption

    @property
    def requires_refuel(
        self,
    ) -> bool:

        return self.fuel is None or self.fuel.fill_percentage <= 15.0

    @property
    def overheating(
        self,
    ) -> bool:

        return self.coolant_efficiency < 0.50

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
                "fuel_consumption": round(
                    self.fuel_consumption,
                    2,
                ),
                "fuel_efficiency": round(
                    self.fuel_efficiency,
                    2,
                ),
                "heat_generation": round(
                    self.heat_generation,
                    2,
                ),
                "coolant_efficiency": round(
                    self.coolant_efficiency,
                    2,
                ),
                "safety_rating": round(
                    self.safety_rating,
                    2,
                ),
                "requires_refuel": self.requires_refuel,
                "overheating": self.overheating,
                "total_power_generated": round(
                    self.total_power_generated,
                    2,
                ),
                "total_fuel_consumed": round(
                    self.total_fuel_consumed,
                    2,
                ),
                "fuel": self.fuel.statistics() if self.fuel is not None else None,
                "power": self.power.statistics(),
                "heat": self.heat.statistics(),
            }
        )

        return stats

    # ========================================================
    # Maintenance
    # ========================================================

    def refuel(
        self,
        amount: float,
    ) -> float:
        """Reject magic refills; delivered colony stock is already reactor stock."""
        if amount <= 0:
            return 0.0
        raise RuntimeError(
            "Reactor fuel cannot be generated locally; deliver fuel into the shared colony inventory."
        )

    def improve_safety(
        self,
        amount: float = 0.05,
    ) -> None:

        self.safety_rating = min(
            1.5,
            self.safety_rating + amount,
        )

    def reduce_safety(
        self,
        amount: float = 0.05,
    ) -> None:

        self.safety_rating = max(
            0.10,
            self.safety_rating - amount,
        )

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        fuel_status = (f"fuel={self.fuel.fill_percentage:.1f}%" if self.fuel is not None
                       else "fuel=unassigned")
        return (
            "Reactor("
            f"health={self.health_percentage:.1f}%, "
            f"output={self.effective_output:.2f} kWh, "
            f"{fuel_status}, "
            f"safety={self.safety_rating:.2f}, "
            f"coolant={self.coolant_efficiency:.2f}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

NuclearReactor = Reactor
