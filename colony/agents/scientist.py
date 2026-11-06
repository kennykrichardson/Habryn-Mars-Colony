"""
scientist.py

Canonical Scientist implementation.

Inheritance

BaseAgent
    ↓
Astronaut
    ↓
Scientist
"""

from __future__ import annotations

import random

from dataclasses import dataclass

from typing import Optional

from colony.agents.astronaut import Astronaut

from colony.agents.base_agent import (
    AgentState,
)

from colony.buildings.laboratory import Laboratory

# ============================================================
# Scientist
# ============================================================


@dataclass
class Scientist(Astronaut):

    specialization: str = "General Research"

    research_speed: float = 12.0

    analysis_speed: float = 8.0

    discovery_chance: float = 0.05

    innovation_bonus: float = 1.0

    assigned_laboratory: Optional[Laboratory] = None

    research_progress: float = 0.0

    projects_completed: int = 0

    discoveries: int = 0

    analyses_completed: int = 0

    technologies_unlocked: int = 0

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        super().__post_init__()

        self.profession = "Scientist"

        self.skill_levels.setdefault(
            "science",
            5,
        )

        self.skill_levels.setdefault(
            "analysis",
            4,
        )

    # ========================================================
    # Assignment
    # ========================================================

    def assign_laboratory(
        self,
        laboratory: Laboratory,
    ) -> None:

        self.assigned_laboratory = laboratory

    # ========================================================
    # Research
    # ========================================================

    def research(
        self,
    ) -> bool:

        if self.assigned_laboratory is None:

            return False

        if not self.assigned_laboratory.operational:

            return False

        self.state = AgentState.RESEARCHING

        progress = (
            self.research_speed
            * self.innovation_bonus
            * (
                self.skill_level(
                    "science",
                )
                / 5
            )
        )

        produced = self.assigned_laboratory.perform_research()

        if produced <= 0:

            return False

        self.research_progress += progress

        self.hours_worked += 1

        self.add_experience(
            5,
        )

        self.improve_skill(
            "science",
            5,
        )

        if self.research_progress >= 100.0:

            self.projects_completed += 1

            self.complete_task()

            self.research_progress = 0.0

        self.state = AgentState.IDLE

        return True

    # ========================================================
    # Analysis
    # ========================================================

    def analyze(
        self,
        sample: object,
    ) -> dict:

        self.state = AgentState.WORKING

        self.analyses_completed += 1

        self.hours_worked += 1

        self.add_experience(
            2,
        )

        self.improve_skill(
            "analysis",
            2,
        )

        self.state = AgentState.IDLE

        return {
            "sample": str(sample),
            "quality": "Analyzed",
            "scientist": self.name,
        }

    # ========================================================
    # Discovery
    # ========================================================

    def discover(
        self,
    ) -> bool:

        chance = self.discovery_chance * (
            self.skill_level(
                "science",
            )
            / 5
        )

        if random.random() > chance:

            return False

        self.discoveries += 1

        self.add_experience(
            20,
        )

        self.unlock_technology()

        return True

    # ========================================================
    # Technology
    # ========================================================

    def unlock_technology(
        self,
    ) -> None:

        self.technologies_unlocked += 1

        self.add_experience(
            15,
        )

    # ========================================================
    # Laboratory
    # ========================================================

    def improve_laboratory(
        self,
    ) -> bool:

        if self.assigned_laboratory is None:

            return False

        self.assigned_laboratory.improve_research_methods()

        self.unlock_technology()

        return True

    # ========================================================
    # Hourly Update
    # ========================================================

    def hourly_update(
        self,
        needs_intensity: float = 1.0,
    ) -> None:

        super().hourly_update(needs_intensity)

        if self.state != AgentState.RESEARCHING:

            return

        self.fatigue = min(
            100.0,
            self.fatigue + 0.40 * needs_intensity,
        )

        self.hunger = min(
            100.0,
            self.hunger + 0.30 * needs_intensity,
        )

        self.thirst = min(
            100.0,
            self.thirst + 0.35 * needs_intensity,
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
                "research_speed": self.research_speed,
                "analysis_speed": self.analysis_speed,
                "discovery_chance": round(
                    self.discovery_chance,
                    4,
                ),
                "innovation_bonus": round(
                    self.innovation_bonus,
                    2,
                ),
                "research_progress": round(
                    self.research_progress,
                    2,
                ),
                "projects_completed": self.projects_completed,
                "discoveries": self.discoveries,
                "analyses_completed": self.analyses_completed,
                "technologies_unlocked": self.technologies_unlocked,
                "assigned_laboratory": (
                    self.assigned_laboratory.name if self.assigned_laboratory else None
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
            "Scientist("
            f"id={self.unique_id}, "
            f"name='{self.name}', "
            f"level={self.level}, "
            f"discoveries={self.discoveries}, "
            f"projects={self.projects_completed}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

ResearchScientist = Scientist
