"""
mine.py

Part 1/6

Canonical Mine.

Extracts raw minerals from the Martian
surface for industrial use.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.minerals import Minerals
from colony.resources.population import Population

# ============================================================
# Mine
# ============================================================


@dataclass
class Mine(BaseBuilding):

    building_id: int = 0

    name: str = "Mine"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Extracts mineral resources from the Martian subsurface."

    extraction_rate: float = 25.0

    power_required: float = 18.0

    workers_required: float = 6.0

    extraction_efficiency: float = 1.0

    ore_quality: float = 100.0

    equipment_condition: float = 100.0

    power: Power = field(
        default_factory=Power,
    )

    minerals: Minerals = field(
        default_factory=Minerals,
    )

    population: Population = field(
        default_factory=Population,
    )

    total_minerals_extracted: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.extract_minerals()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        self.equipment_condition = min(
            100.0,
            self.equipment_condition,
        )

    # ========================================================
    # Mining
    # ========================================================

    def extract_minerals(
        self,
    ) -> float:

        if (
            not self.operational
            or self.power.current_amount < self.power_required
            or self.population.current_amount < self.workers_required
        ):

            return 0.0

        self.power.consume(
            self.power_required,
        )

        extracted = (
            self.extraction_rate
            * self.efficiency
            * self.extraction_efficiency
            * (self.equipment_condition / 100.0)
            * (self.ore_quality / 100.0)
        )

        produced = self.minerals.generate(
            extracted,
        )

        self.total_minerals_extracted += produced

        return produced

    # ========================================================
    # Mining Management
    # ========================================================

    def repair_equipment(
        self,
        amount: float = 5.0,
    ) -> None:

        self.equipment_condition = min(
            100.0,
            self.equipment_condition + amount,
        )

    def equipment_failure(
        self,
        damage: float = 5.0,
    ) -> None:

        self.equipment_condition = max(
            0.0,
            self.equipment_condition - damage,
        )

    def improve_extraction(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.extraction_efficiency = min(
            2.0,
            self.extraction_efficiency + bonus,
        )

    def assign_workers(
        self,
        workers: float,
    ) -> None:

        self.workers_required = max(
            1.0,
            workers,
        )

    def discover_rich_deposit(
        self,
        bonus: float = 5.0,
    ) -> None:

        self.ore_quality = min(
            150.0,
            self.ore_quality + bonus,
        )

    def exhaust_deposit(
        self,
        amount: float = 2.0,
    ) -> None:

        self.ore_quality = max(
            25.0,
            self.ore_quality - amount,
        )

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_output(
        self,
    ) -> float:

        return (
            self.extraction_rate
            * self.efficiency
            * self.extraction_efficiency
            * (self.equipment_condition / 100.0)
            * (self.ore_quality / 100.0)
        )

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_output / self.power_required

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

        return self.equipment_condition < 65.0

    @property
    def rich_deposit(
        self,
    ) -> bool:

        return self.ore_quality >= 120.0

    @property
    def depleted(
        self,
    ) -> bool:

        return self.ore_quality <= 35.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "extraction_rate": round(
                    self.extraction_rate,
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
                "workers_required": round(
                    self.workers_required,
                    2,
                ),
                "extraction_efficiency": round(
                    self.extraction_efficiency,
                    2,
                ),
                "ore_quality": round(
                    self.ore_quality,
                    2,
                ),
                "equipment_condition": round(
                    self.equipment_condition,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "worker_efficiency": round(
                    self.worker_efficiency,
                    2,
                ),
                "requires_maintenance": self.requires_maintenance,
                "rich_deposit": self.rich_deposit,
                "depleted": self.depleted,
                "total_minerals_extracted": round(
                    self.total_minerals_extracted,
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
            "Mine("
            f"health={self.health_percentage:.1f}%, "
            f"ore={self.ore_quality:.1f}%, "
            f"equipment={self.equipment_condition:.1f}%, "
            f"output={self.effective_output:.2f} kg/h"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

MiningFacility = Mine
