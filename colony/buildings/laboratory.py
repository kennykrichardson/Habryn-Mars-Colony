"""
laboratory.py

Part 1/6

Canonical Laboratory.

Produces Science Points for the colony by
consuming power and employing researchers.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.science_points import SciencePoints
from colony.resources.population import Population

# ============================================================
# Laboratory
# ============================================================


@dataclass
class Laboratory(BaseBuilding):

    building_id: int = 0

    name: str = "Research Laboratory"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = (
        "Scientific research facility producing technological advancements."
    )

    science_output: float = 20.0

    power_required: float = 12.0

    researchers_required: float = 5.0

    research_efficiency: float = 1.0

    equipment_condition: float = 100.0

    power: Power = field(
        default_factory=Power,
    )

    science: SciencePoints = field(
        default_factory=SciencePoints,
    )

    population: Population = field(
        default_factory=Population,
    )

    total_science_generated: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.perform_research()

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
    # Research
    # ========================================================

    def perform_research(
        self,
    ) -> float:

        if (
            not self.operational
            or self.power.current_amount < self.power_required
            or self.population.current_amount < self.researchers_required
        ):

            return 0.0

        self.power.consume(
            self.power_required,
        )

        generated = (
            self.science_output
            * self.efficiency
            * self.research_efficiency
            * (self.equipment_condition / 100.0)
        )

        produced = self.science.generate(
            generated,
        )

        self.total_science_generated += produced

        return produced

        # ========================================================

    # Research Management
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

    def improve_research_methods(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.research_efficiency = min(
            2.0,
            self.research_efficiency + bonus,
        )

    def assign_researchers(
        self,
        researchers: float,
    ) -> None:

        self.researchers_required = max(
            1.0,
            researchers,
        )

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_output(
        self,
    ) -> float:

        return (
            self.science_output
            * self.efficiency
            * self.research_efficiency
            * (self.equipment_condition / 100.0)
        )

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_output / self.power_required

    @property
    def researcher_efficiency(
        self,
    ) -> float:

        if self.researchers_required <= 0:

            return 0.0

        return self.effective_output / self.researchers_required

    @property
    def requires_maintenance(
        self,
    ) -> bool:

        return self.equipment_condition < 60.0

    @property
    def fully_operational(
        self,
    ) -> bool:

        return self.equipment_condition >= 95.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "science_output": round(
                    self.science_output,
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
                "researchers_required": round(
                    self.researchers_required,
                    2,
                ),
                "research_efficiency": round(
                    self.research_efficiency,
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
                "researcher_efficiency": round(
                    self.researcher_efficiency,
                    2,
                ),
                "requires_maintenance": self.requires_maintenance,
                "fully_operational": self.fully_operational,
                "total_science_generated": round(
                    self.total_science_generated,
                    2,
                ),
                "power": self.power.statistics(),
                "science": self.science.statistics(),
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
            "Laboratory("
            f"health={self.health_percentage:.1f}%, "
            f"equipment={self.equipment_condition:.1f}%, "
            f"output={self.effective_output:.2f} SP/h, "
            f"research={self.research_efficiency:.2f}x"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

ResearchLaboratory = Laboratory
