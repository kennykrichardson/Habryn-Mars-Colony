"""
workshop.py

Part 1/6

Canonical Workshop.

Manufactures tools, spare parts and equipment
required by the colony.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.minerals import Minerals
from colony.resources.population import Population

# ============================================================
# Workshop
# ============================================================


@dataclass
class Workshop(BaseBuilding):

    building_id: int = 0

    name: str = "Workshop"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Manufactures equipment and performs colony maintenance."

    manufacturing_rate: float = 15.0

    power_required: float = 15.0

    mineral_consumption: float = 8.0

    workers_required: float = 4.0

    manufacturing_efficiency: float = 1.0

    machine_condition: float = 100.0

    power: Power = field(
        default_factory=Power,
    )

    minerals: Minerals = field(
        default_factory=Minerals,
    )

    population: Population = field(
        default_factory=Population,
    )

    total_materials_processed: float = 0.0

    total_items_manufactured: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.manufacture()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        self.machine_condition = min(
            100.0,
            self.machine_condition,
        )

    # ========================================================
    # Manufacturing
    # ========================================================

    def manufacture(
        self,
    ) -> float:

        if (
            not self.operational
            or self.power.current_amount < self.power_required
            or self.minerals.current_amount < self.mineral_consumption
            or self.population.current_amount < self.workers_required
        ):

            return 0.0

        self.power.consume(
            self.power_required,
        )

        self.minerals.consume(
            self.mineral_consumption,
        )

        produced = (
            self.manufacturing_rate
            * self.efficiency
            * self.manufacturing_efficiency
            * (self.machine_condition / 100.0)
        )

        self.total_materials_processed += self.mineral_consumption

        self.total_items_manufactured += produced

        return produced

    # ========================================================
    # Manufacturing Management
    # ========================================================

    def repair_machines(
        self,
        amount: float = 5.0,
    ) -> None:

        self.machine_condition = min(
            100.0,
            self.machine_condition + amount,
        )

    def machine_breakdown(
        self,
        damage: float = 5.0,
    ) -> None:

        self.machine_condition = max(
            0.0,
            self.machine_condition - damage,
        )

    def improve_manufacturing(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.manufacturing_efficiency = min(
            2.0,
            self.manufacturing_efficiency + bonus,
        )

    def assign_workers(
        self,
        workers: float,
    ) -> None:

        self.workers_required = max(
            1.0,
            workers,
        )

    def upgrade_machines(
        self,
        bonus: float = 1.0,
    ) -> None:

        self.manufacturing_rate += bonus

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_output(
        self,
    ) -> float:

        return (
            self.manufacturing_rate
            * self.efficiency
            * self.manufacturing_efficiency
            * (self.machine_condition / 100.0)
        )

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_output / self.power_required

    @property
    def mineral_efficiency(
        self,
    ) -> float:

        if self.mineral_consumption <= 0:

            return 0.0

        return self.effective_output / self.mineral_consumption

    @property
    def worker_efficiency(
        self,
    ) -> float:

        if self.workers_required <= 0:

            return 0.0

        return self.effective_output / self.workers_required

    @property
    def requires_maintenance(
        self,
    ) -> bool:

        return self.machine_condition < 65.0

    @property
    def fully_operational(
        self,
    ) -> bool:

        return self.machine_condition >= 95.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "manufacturing_rate": round(
                    self.manufacturing_rate,
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
                "mineral_consumption": round(
                    self.mineral_consumption,
                    2,
                ),
                "workers_required": round(
                    self.workers_required,
                    2,
                ),
                "manufacturing_efficiency": round(
                    self.manufacturing_efficiency,
                    2,
                ),
                "machine_condition": round(
                    self.machine_condition,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "mineral_efficiency": round(
                    self.mineral_efficiency,
                    2,
                ),
                "worker_efficiency": round(
                    self.worker_efficiency,
                    2,
                ),
                "requires_maintenance": self.requires_maintenance,
                "fully_operational": self.fully_operational,
                "total_materials_processed": round(
                    self.total_materials_processed,
                    2,
                ),
                "total_items_manufactured": round(
                    self.total_items_manufactured,
                    2,
                ),
                "power": self.power.statistics(),
                "minerals": self.minerals.statistics(),
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
            "Workshop("
            f"health={self.health_percentage:.1f}%, "
            f"machines={self.machine_condition:.1f}%, "
            f"output={self.effective_output:.2f}/h, "
            f"efficiency={self.manufacturing_efficiency:.2f}x"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

FabricationWorkshop = Workshop
