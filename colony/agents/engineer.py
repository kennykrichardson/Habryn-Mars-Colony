"""
engineer.py

Canonical Engineer implementation.

Inheritance

BaseAgent
    ↓
Astronaut
    ↓
Engineer
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import Optional

from colony.agents.astronaut import Astronaut

from colony.agents.base_agent import (
    AgentState,
)

from colony.buildings.base_building import BaseBuilding

# ============================================================
# Engineer
# ============================================================


@dataclass
class Engineer(Astronaut):

    specialization: str = "General"

    repair_speed: float = 8.0

    build_speed: float = 6.0

    maintenance_efficiency: float = 1.0

    construction_quality: float = 1.0

    current_structure: Optional[BaseBuilding] = None

    repair_progress: float = 0.0

    build_progress: float = 0.0

    structures_repaired: int = 0

    structures_built: int = 0

    maintenance_completed: int = 0

    emergency_repairs: int = 0

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        super().__post_init__()

        self.profession = "Engineer"

        self.skill_levels.setdefault(
            "engineering",
            5,
        )

        self.skill_levels.setdefault(
            "construction",
            4,
        )

    # ========================================================
    # Repair
    # ========================================================

    def repair(
        self,
    ) -> bool:

        if self.current_structure is None:

            return False

        integrity = self.current_structure.integrity

        if integrity >= 100.0:

            return False

        self.state = AgentState.REPAIRING

        repair_amount = (
            self.repair_speed
            * self.maintenance_efficiency
            * (
                self.skill_level(
                    "engineering",
                )
                / 5
            )
        )

        self.current_structure.repair(
            repair_amount,
        )

        self.repair_progress += repair_amount

        self.hours_worked += 1

        self.add_experience(4)

        self.improve_skill(
            "engineering",
            5,
        )

        if self.current_structure.integrity >= 100.0:

            self.structures_repaired += 1

            self.complete_task()

            self.current_structure = None

            self.state = AgentState.IDLE

        return True

    # ========================================================
    # Build
    # ========================================================

    def build(
        self,
        structure: BaseBuilding,
    ) -> bool:

        self.state = AgentState.BUILDING

        self.current_structure = structure

        build_amount = (
            self.build_speed
            * (
                self.skill_level(
                    "construction",
                )
                / 5
            )
            * self.construction_quality
        )

        self.build_progress += build_amount

        self.hours_worked += 1

        self.add_experience(5)

        self.improve_skill(
            "construction",
            5,
        )

        if self.build_progress >= 100.0:

            self.structures_built += 1

            self.complete_task()

            self.build_progress = 0.0

            self.current_structure = None

            self.state = AgentState.IDLE

            return True

        return False

    # ========================================================
    # Maintenance
    # ========================================================

    def maintain(
        self,
        structure: BaseBuilding,
    ) -> bool:

        structure.maintain(
            4.0 * self.maintenance_efficiency,
        )

        self.maintenance_completed += 1

        self.hours_worked += 1

        self.add_experience(2)

        self.improve_skill(
            "engineering",
            2,
        )

        return True

    # ========================================================
    # Emergency Repair
    # ========================================================

    def emergency_repair(
        self,
        structure: BaseBuilding,
    ) -> None:

        bonus = self.repair_speed * 1.5

        structure.repair(
            bonus,
        )

        self.emergency_repairs += 1

        self.structures_repaired += 1

        self.complete_task()

        self.change_stress(
            4.0,
        )

    # ========================================================
    # Inspection
    # ========================================================

    def inspect(
        self,
        structure: BaseBuilding,
    ) -> dict:

        return {
            "integrity": round(
                structure.integrity,
                2,
            ),
            "maintenance": round(
                structure.maintenance,
                2,
            ),
            "powered": structure.powered,
            "state": structure.state.value,
            "efficiency": round(
                structure.efficiency,
                2,
            ),
        }

    # ========================================================
    # Upgrade
    # ========================================================

    def upgrade_structure(
        self,
        structure: BaseBuilding,
    ) -> None:

        structure.upgrade()

        self.add_experience(
            8,
        )

        self.improve_skill(
            "engineering",
            4,
        )

    # ========================================================
    # Hourly Update
    # ========================================================

    def hourly_update(
        self,
        needs_intensity: float = 1.0,
    ) -> None:

        super().hourly_update(needs_intensity)

        if self.state not in (
            AgentState.REPAIRING,
            AgentState.BUILDING,
        ):

            return

        self.fatigue = min(
            100.0,
            self.fatigue + 0.6 * needs_intensity,
        )

        self.hunger = min(
            100.0,
            self.hunger + 0.4 * needs_intensity,
        )

        self.thirst = min(
            100.0,
            self.thirst + 0.5 * needs_intensity,
        )

        self.change_stress(
            0.2 * needs_intensity,
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
                "repair_speed": self.repair_speed,
                "build_speed": self.build_speed,
                "maintenance_efficiency": self.maintenance_efficiency,
                "construction_quality": self.construction_quality,
                "structures_repaired": self.structures_repaired,
                "structures_built": self.structures_built,
                "maintenance_completed": self.maintenance_completed,
                "emergency_repairs": self.emergency_repairs,
                "repair_progress": round(
                    self.repair_progress,
                    2,
                ),
                "build_progress": round(
                    self.build_progress,
                    2,
                ),
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
            "Engineer("
            f"id={self.unique_id}, "
            f"name='{self.name}', "
            f"level={self.level}, "
            f"repairs={self.structures_repaired}, "
            f"builds={self.structures_built}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

ConstructionEngineer = Engineer
