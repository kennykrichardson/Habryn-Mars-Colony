"""
launch_pad.py

Part 1/6

Canonical Launch Pad.

Handles launches, landings, cargo logistics,
crew transport and orbital missions.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.fuel import Fuel
from colony.resources.population import Population

# ============================================================
# Launch Pad
# ============================================================


@dataclass
class LaunchPad(BaseBuilding):

    building_id: int = 0

    name: str = "Launch Pad"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = (
        "Launches spacecraft, receives cargo and supports orbital operations."
    )

    launch_capacity: int = 2

    launch_efficiency: float = 1.0

    power_required: float = 40.0

    fuel_required: float = 80.0

    pad_condition: float = 100.0

    traffic_efficiency: float = 1.0

    power: Power = field(
        default_factory=Power,
    )

    fuel: Fuel | None = None

    population: Population = field(
        default_factory=Population,
    )

    total_launches: int = 0

    total_landings: int = 0

    total_cargo_processed: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.manage_launch_operations()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        self.pad_condition = min(
            100.0,
            self.pad_condition,
        )

    # ========================================================
    # Launch Operations
    # ========================================================

    def manage_launch_operations(
        self,
    ) -> float:

        if (
            not self.operational
            or self.power.current_amount < self.power_required
            or self.fuel is None
            or self.fuel.current_amount < self.fuel_required
        ):

            return 0.0

        self.power.consume(
            self.power_required,
        )

        self.fuel.consume(
            self.fuel_required,
        )

        throughput = (
            self.launch_capacity
            * self.launch_efficiency
            * self.traffic_efficiency
            * self.efficiency
            * (self.pad_condition / 100.0)
        )

        self.total_launches += int(
            throughput,
        )

        self.total_cargo_processed += throughput * 100.0

        return throughput

    # ========================================================
    # Launch Management
    # ========================================================

    def repair_pad(
        self,
        amount: float = 5.0,
    ) -> None:

        self.pad_condition = min(
            100.0,
            self.pad_condition + amount,
        )

    def pad_damage(
        self,
        amount: float = 5.0,
    ) -> None:

        self.pad_condition = max(
            0.0,
            self.pad_condition - amount,
        )

    def improve_launch_systems(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.launch_efficiency = min(
            2.0,
            self.launch_efficiency + bonus,
        )

    def improve_traffic_control(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.traffic_efficiency = min(
            2.0,
            self.traffic_efficiency + bonus,
        )

    def expand_launch_capacity(
        self,
        pads: int = 1,
    ) -> None:

        self.launch_capacity += max(
            0,
            pads,
        )

    def record_landing(
        self,
        cargo_mass: float = 0.0,
    ) -> None:

        self.total_landings += 1

        self.total_cargo_processed += max(
            0.0,
            cargo_mass,
        )

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_launch_rate(
        self,
    ) -> float:

        return (
            self.launch_capacity
            * self.launch_efficiency
            * self.traffic_efficiency
            * self.efficiency
            * (self.pad_condition / 100.0)
        )

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_launch_rate / self.power_required

    @property
    def fuel_efficiency(
        self,
    ) -> float:

        if self.fuel_required <= 0:

            return 0.0

        return self.effective_launch_rate / self.fuel_required

    @property
    def requires_maintenance(
        self,
    ) -> bool:

        return self.pad_condition < 65.0

    @property
    def fully_operational(
        self,
    ) -> bool:

        return self.operational and self.pad_condition >= 95.0

    @property
    def launch_ready(
        self,
    ) -> bool:

        return (
            self.operational
            and self.power.current_amount >= self.power_required
            and self.fuel is not None
            and self.fuel.current_amount >= self.fuel_required
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
                "launch_capacity": self.launch_capacity,
                "effective_launch_rate": round(
                    self.effective_launch_rate,
                    2,
                ),
                "launch_efficiency": round(
                    self.launch_efficiency,
                    2,
                ),
                "traffic_efficiency": round(
                    self.traffic_efficiency,
                    2,
                ),
                "power_required": round(
                    self.power_required,
                    2,
                ),
                "fuel_required": round(
                    self.fuel_required,
                    2,
                ),
                "pad_condition": round(
                    self.pad_condition,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "fuel_efficiency": round(
                    self.fuel_efficiency,
                    2,
                ),
                "requires_maintenance": self.requires_maintenance,
                "fully_operational": self.fully_operational,
                "launch_ready": self.launch_ready,
                "total_launches": self.total_launches,
                "total_landings": self.total_landings,
                "total_cargo_processed": round(
                    self.total_cargo_processed,
                    2,
                ),
                "power": self.power.statistics(),
                "fuel": self.fuel.statistics() if self.fuel is not None else None,
                "population": self.population.statistics(),
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
            "LaunchPad("
            f"health={self.health_percentage:.1f}%, "
            f"pad={self.pad_condition:.1f}%, "
            f"launches={self.launch_capacity}, "
            f"ready={self.launch_ready}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Spaceport = LaunchPad
