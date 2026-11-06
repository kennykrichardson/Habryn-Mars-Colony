"""
medic.py

Canonical Medic implementation.

Inheritance

BaseAgent
    ↓
Astronaut
    ↓
Medic
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import Optional

from colony.agents.astronaut import Astronaut

from colony.agents.base_agent import (
    AgentState,
)

# ============================================================
# Medic
# ============================================================


@dataclass
class Medic(Astronaut):

    specialization: str = "General Medicine"

    healing_rate: float = 12.0

    treatment_speed: float = 8.0

    diagnosis_speed: float = 15.0

    radiation_treatment_rate: float = 3.0

    current_patient: Optional[Astronaut] = None

    patients_treated: int = 0

    diagnoses_completed: int = 0

    emergencies_handled: int = 0

    radiation_cases: int = 0

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        super().__post_init__()

        self.profession = "Medic"

        self.skill_levels.setdefault(
            "medicine",
            5,
        )

        self.skill_levels.setdefault(
            "diagnosis",
            4,
        )

    # ========================================================
    # Assignment
    # ========================================================

    def assign_patient(
        self,
        patient: Astronaut,
    ) -> None:

        self.current_patient = patient

    # ========================================================
    # Healing
    # ========================================================

    def heal_patient(
        self,
    ) -> bool:

        if self.current_patient is None:

            return False

        self.state = AgentState.WORKING

        amount = self.healing_rate * (
            self.skill_level(
                "medicine",
            )
            / 5
        )

        self.current_patient.heal(
            amount,
        )

        self.hours_worked += 1

        self.add_experience(
            5,
        )

        self.improve_skill(
            "medicine",
            5,
        )

        if self.current_patient.health >= 100.0:

            self.patients_treated += 1

            self.complete_task()

            self.current_patient = None

        self.state = AgentState.IDLE

        return True

    # ========================================================
    # Radiation Treatment
    # ========================================================

    def treat_radiation(
        self,
        patient: Astronaut,
    ) -> None:

        patient.radiation = max(
            0.0,
            patient.radiation - self.radiation_treatment_rate,
        )

        self.radiation_cases += 1

        self.hours_worked += 1

        self.add_experience(
            4,
        )

        self.improve_skill(
            "medicine",
            2,
        )

    # ========================================================
    # Diagnosis
    # ========================================================

    def diagnose(
        self,
        patient: Astronaut,
    ) -> dict:

        self.state = AgentState.WORKING

        self.diagnoses_completed += 1

        self.hours_worked += 1

        self.add_experience(
            2,
        )

        self.improve_skill(
            "diagnosis",
            2,
        )

        self.state = AgentState.IDLE

        return {
            "health": round(
                patient.health,
                2,
            ),
            "oxygen": round(
                patient.oxygen,
                2,
            ),
            "hunger": round(
                patient.hunger,
                2,
            ),
            "thirst": round(
                patient.thirst,
                2,
            ),
            "fatigue": round(
                patient.fatigue,
                2,
            ),
            "radiation": round(
                patient.radiation,
                2,
            ),
            "alive": patient.alive,
        }

    # ========================================================
    # Emergency Response
    # ========================================================

    def emergency_response(
        self,
        patient: Astronaut,
    ) -> None:

        self.state = AgentState.WORKING

        self.emergencies_handled += 1

        patient.heal(
            20.0,
        )

        self.add_experience(
            10,
        )

        self.complete_task()

        self.change_stress(
            0.5,
        )

        self.state = AgentState.IDLE

    # ========================================================
    # Health Inspection
    # ========================================================

    def inspect_colony_health(
        self,
        astronauts: list[Astronaut],
    ) -> dict:

        healthy = 0

        injured = 0

        critical = 0

        for astronaut in astronauts:

            if astronaut.health >= 80.0:

                healthy += 1

            elif astronaut.health >= 40.0:

                injured += 1

            else:

                critical += 1

        return {
            "healthy": healthy,
            "injured": injured,
            "critical": critical,
            "population": len(
                astronauts,
            ),
        }

    # ========================================================
    # Hourly Update
    # ========================================================

    def hourly_update(
        self,
        needs_intensity: float = 1.0,
    ) -> None:

        super().hourly_update(needs_intensity)

        if self.state != AgentState.WORKING:

            return

        self.fatigue = min(
            100.0,
            self.fatigue + 0.40 * needs_intensity,
        )

        self.hunger = min(
            100.0,
            self.hunger + 0.25 * needs_intensity,
        )

        self.thirst = min(
            100.0,
            self.thirst + 0.30 * needs_intensity,
        )

        self.change_stress(
            0.15 * needs_intensity,
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
                "specialization": self.specialization,
                "healing_rate": self.healing_rate,
                "treatment_speed": self.treatment_speed,
                "diagnosis_speed": self.diagnosis_speed,
                "radiation_treatment_rate": self.radiation_treatment_rate,
                "patients_treated": self.patients_treated,
                "diagnoses_completed": self.diagnoses_completed,
                "emergencies_handled": self.emergencies_handled,
                "radiation_cases": self.radiation_cases,
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
            "Medic("
            f"id={self.unique_id}, "
            f"name='{self.name}', "
            f"level={self.level}, "
            f"patients={self.patients_treated}, "
            f"emergencies={self.emergencies_handled}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

MedicalOfficer = Medic
