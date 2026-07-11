"""
farmer.py

Canonical Farmer implementation.

Inheritance

BaseAgent
    ↓
Astronaut
    ↓
Farmer
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import Optional

from colony.agents.astronaut import Astronaut

from colony.agents.base_agent import (
    AgentState,
)

from colony.buildings.greenhouse import Greenhouse

# ============================================================
# Farmer
# ============================================================


@dataclass
class Farmer(Astronaut):

    specialization: str = "Hydroponics"

    planting_speed: float = 10.0

    harvesting_speed: float = 12.0

    irrigation_efficiency: float = 1.0

    crop_care_bonus: float = 1.0

    assigned_greenhouse: Optional[
        Greenhouse
    ] = None

    harvest_progress: float = 0.0

    crops_planted: int = 0

    harvests_completed: int = 0

    plants_watered: int = 0

    crop_failures_prevented: int = 0

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        super().__post_init__()

        self.profession = "Farmer"

        self.skill_levels.setdefault(
            "agriculture",
            5,
        )

        self.skill_levels.setdefault(
            "botany",
            4,
        )

    # ========================================================
    # Assignment
    # ========================================================

    def assign_greenhouse(
        self,
        greenhouse: Greenhouse,
    ) -> None:

        self.assigned_greenhouse = greenhouse

    # ========================================================
    # Planting
    # ========================================================

    def plant(
        self,
    ) -> bool:

        if self.assigned_greenhouse is None:

            return False

        self.state = AgentState.WORKING

        self.crops_planted += 1

        self.hours_worked += 1

        self.complete_task()

        self.add_experience(
            4,
        )

        self.improve_skill(
            "agriculture",
            5,
        )

        self.state = AgentState.IDLE

        return True
    
    # ========================================================
    # Watering
    # ========================================================

    def water(
        self,
    ) -> bool:

        if self.assigned_greenhouse is None:

            return False

        self.state = AgentState.WORKING

        self.assigned_greenhouse.irrigate(

            5.0,

        )

        self.plants_watered += 1

        self.hours_worked += 1

        self.add_experience(

            2,

        )

        self.improve_skill(

            "agriculture",

            2,

        )

        self.state = AgentState.IDLE

        return True

    # ========================================================
    # Harvest
    # ========================================================

    def harvest(
        self,
        food_system,
        oxygen_system,
    ) -> bool:

        if self.assigned_greenhouse is None:

            return False

        self.state = AgentState.WORKING

        harvested = self.assigned_greenhouse.grow_food()

        if harvested <= 0:

            self.state = AgentState.IDLE

            return False

        self.harvests_completed += 1

        self.complete_task()

        self.add_experience(

            6,

        )

        self.improve_skill(

            "agriculture",

            4,

        )

        self.state = AgentState.IDLE

        return True
    
    # ========================================================
    # Crop Inspection
    # ========================================================

    def inspect_crop(
        self,
    ) -> dict:

        if self.assigned_greenhouse is None:

            return {}

        greenhouse = self.assigned_greenhouse

        return {

            "crop_health": round(

                greenhouse.crop_health,

                2,

            ),

            "growth": round(

                greenhouse.growth_bonus,

                2,

            ),

            "integrity": round(

                greenhouse.integrity,

                2,

            ),

            "maintenance": round(

                greenhouse.maintenance,

                2,

            ),

            "state": greenhouse.state.value,

        }

    # ========================================================
    # Crop Recovery
    # ========================================================

    def rescue_crop(
        self,
    ) -> bool:

        if self.assigned_greenhouse is None:

            return False

        greenhouse = self.assigned_greenhouse

        if greenhouse.crop_health >= 80.0:

            return False

        greenhouse.crop_health = min(

            100.0,

            greenhouse.crop_health + 15.0,

        )

        self.crop_failures_prevented += 1

        self.add_experience(

            8,

        )

        self.improve_skill(

            "botany",

            4,

        )

        return True

    # ========================================================
    # Greenhouse Maintenance
    # ========================================================

    def maintain_greenhouse(
        self,
    ) -> bool:

        if self.assigned_greenhouse is None:

            return False

        self.assigned_greenhouse.maintain(

            5.0,

        )

        self.add_experience(

            2,

        )

        return True
    
    # ========================================================
    # Hourly Update
    # ========================================================

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

        if self.state != AgentState.WORKING:

            return

        self.fatigue = min(

            100.0,

            self.fatigue + 0.55,

        )

        self.hunger = min(

            100.0,

            self.hunger + 0.35,

        )

        self.thirst = min(

            100.0,

            self.thirst + 0.45,

        )

        self.change_stress(

            0.10,

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

                "planting_speed": self.planting_speed,

                "harvesting_speed": self.harvesting_speed,

                "irrigation_efficiency": self.irrigation_efficiency,

                "crop_care_bonus": self.crop_care_bonus,

                "crops_planted": self.crops_planted,

                "harvests_completed": self.harvests_completed,

                "plants_watered": self.plants_watered,

                "crop_failures_prevented": self.crop_failures_prevented,

                "harvest_progress": round(

                    self.harvest_progress,

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

            "Farmer("

            f"id={self.unique_id}, "

            f"name='{self.name}', "

            f"level={self.level}, "

            f"harvests={self.harvests_completed}, "

            f"crops={self.crops_planted}"

            ")"

        )


# ============================================================
# Canonical Alias
# ============================================================

AgriculturalSpecialist = Farmer