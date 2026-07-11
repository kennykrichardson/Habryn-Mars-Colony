"""
medical_bay.py

Part 1/6

Canonical Medical Bay.

Provides healthcare, treats injuries,
improves colonist health and morale.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.population import Population
from colony.resources.morale import Morale

# ============================================================
# Medical Bay
# ============================================================


@dataclass
class MedicalBay(BaseBuilding):

    building_id: int = 0

    name: str = "Medical Bay"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Provides healthcare and emergency medical services."

    healing_rate: float = 8.0

    patients_capacity: int = 20

    power_required: float = 10.0

    medicine_efficiency: float = 1.0

    sanitation: float = 100.0

    power: Power = field(
        default_factory=Power,
    )

    population: Population = field(
        default_factory=Population,
    )

    morale: Morale = field(
        default_factory=Morale,
    )

    total_patients_treated: int = 0

    total_healing_provided: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.treat_patients()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        self.sanitation = min(
            100.0,
            self.sanitation,
        )

    # ========================================================
    # Medical Operations
    # ========================================================

    def treat_patients(
        self,
    ) -> float:

        if not self.operational or self.power.current_amount < self.power_required:

            return 0.0

        self.power.consume(
            self.power_required,
        )

        healing = (
            self.healing_rate
            * self.efficiency
            * self.medicine_efficiency
            * (self.sanitation / 100.0)
        )

        self.total_healing_provided += healing

        self.total_patients_treated += int(
            min(
                healing,
                self.patients_capacity,
            )
        )

        self.morale.generate(
            healing * 0.10,
        )

        return healing

        # ========================================================

    # Medical Management
    # ========================================================

    def sterilize(
        self,
        bonus: float = 5.0,
    ) -> None:

        self.sanitation = min(
            100.0,
            self.sanitation + bonus,
        )

    def contamination(
        self,
        amount: float = 5.0,
    ) -> None:

        self.sanitation = max(
            0.0,
            self.sanitation - amount,
        )

    def improve_medicine(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.medicine_efficiency = min(
            2.0,
            self.medicine_efficiency + bonus,
        )

    def admit_patients(
        self,
        patients: int,
    ) -> int:

        admitted = min(
            patients,
            self.patients_capacity,
        )

        self.total_patients_treated += admitted

        return admitted

    def discharge_patients(
        self,
        patients: int,
    ) -> int:

        return max(
            0,
            patients,
        )

        # ========================================================

    # Status
    # ========================================================

    @property
    def effective_healing(
        self,
    ) -> float:

        return (
            self.healing_rate
            * self.efficiency
            * self.medicine_efficiency
            * (self.sanitation / 100.0)
        )

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_healing / self.power_required

    @property
    def requires_cleaning(
        self,
    ) -> bool:

        return self.sanitation < 70.0

    @property
    def overloaded(
        self,
    ) -> bool:

        return self.total_patients_treated > self.patients_capacity

    @property
    def fully_operational(
        self,
    ) -> bool:

        return self.sanitation >= 95.0 and self.operational

        # ========================================================

    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "healing_rate": round(
                    self.healing_rate,
                    2,
                ),
                "effective_healing": round(
                    self.effective_healing,
                    2,
                ),
                "patients_capacity": self.patients_capacity,
                "power_required": round(
                    self.power_required,
                    2,
                ),
                "medicine_efficiency": round(
                    self.medicine_efficiency,
                    2,
                ),
                "sanitation": round(
                    self.sanitation,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "requires_cleaning": self.requires_cleaning,
                "overloaded": self.overloaded,
                "fully_operational": self.fully_operational,
                "total_patients_treated": self.total_patients_treated,
                "total_healing_provided": round(
                    self.total_healing_provided,
                    2,
                ),
                "power": self.power.statistics(),
                "population": self.population.statistics(),
                "morale": self.morale.statistics(),
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
            "MedicalBay("
            f"health={self.health_percentage:.1f}%, "
            f"sanitation={self.sanitation:.1f}%, "
            f"healing={self.effective_healing:.2f}/h, "
            f"patients={self.patients_capacity}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Hospital = MedicalBay
