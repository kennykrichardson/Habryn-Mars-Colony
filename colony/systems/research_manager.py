"""
research_manager.py

Part 1/4

Canonical Research Manager.

Responsible for all colony research.

Owns

- research queue
- active research
- completed technologies
- researcher assignments

Does NOT perform research.

Scientists perform research.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import Any

from colony.systems.base_manager import BaseManager

# ============================================================
# Research Project
# ============================================================


@dataclass(slots=True)
class ResearchProject:

    name: str

    description: str

    required_points: float

    progress: float = 0.0

    priority: int = 1

    assigned_scientist: Any | None = None

    completed: bool = False

    unlocked: bool = False


# ============================================================
# Research Manager
# ============================================================


@dataclass
class ResearchManager(BaseManager):

    name: str = "Research Manager"

    research_queue: deque[ResearchProject] = field(default_factory=deque)

    active_projects: list[ResearchProject] = field(default_factory=list)

    completed_projects: list[ResearchProject] = field(default_factory=list)

    research_points: float = 0.0

    # ========================================================
    # Projects
    # ========================================================

    def create_project(
        self,
        name: str,
        description: str,
        required_points: float,
        priority: int = 1,
    ) -> ResearchProject:

        project = ResearchProject(
            name=name,
            description=description,
            required_points=required_points,
            priority=priority,
        )

        self.research_queue.append(
            project,
        )

        return project

    # ========================================================
    # Assignment
    # ========================================================

    def assign_project(
        self,
        scientist: Any,
        project: ResearchProject,
    ) -> bool:

        if project.assigned_scientist is not None:

            return False

        project.assigned_scientist = scientist

        self.active_projects.append(
            project,
        )

        if project in self.research_queue:

            self.research_queue.remove(
                project,
            )

        return True

    # ========================================================
    # Progress
    # ========================================================

    def add_research(
        self,
        points: float,
    ) -> None:

        self.research_points += max(
            0.0,
            points,
        )

    def advance_project(
        self,
        project: ResearchProject,
        points: float,
    ) -> None:

        if project.completed:

            return

        project.progress += points

        if project.progress >= project.required_points:

            self.complete_project(
                project,
            )

    # ========================================================
    # Completion
    # ========================================================

    def complete_project(
        self,
        project: ResearchProject,
    ) -> None:

        project.progress = project.required_points

        project.completed = True

        project.unlocked = True

        if project in self.active_projects:

            self.active_projects.remove(
                project,
            )

        self.completed_projects.append(
            project,
        )

    # ========================================================
    # Queries
    # ========================================================

    def next_project(
        self,
    ) -> ResearchProject | None:

        if not self.research_queue:

            return None

        project = max(
            self.research_queue,
            key=lambda p: p.priority,
        )

        self.research_queue.remove(
            project,
        )

        self.active_projects.append(
            project,
        )

        return project

    def pending_projects(
        self,
    ) -> list[ResearchProject]:

        return list(
            self.research_queue,
        )

        # ========================================================

    # Update Loop
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

        self.step()

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "research_points": round(
                    self.research_points,
                    2,
                ),
                "queued_projects": len(
                    self.research_queue,
                ),
                "active_projects": len(
                    self.active_projects,
                ),
                "completed_projects": len(
                    self.completed_projects,
                ),
            }
        )

        return stats

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data.update(
            {
                "research_points": self.research_points,
                "completed_projects": [
                    {
                        "name": project.name,
                        "description": project.description,
                        "required_points": project.required_points,
                        "progress": project.progress,
                        "priority": project.priority,
                        "completed": project.completed,
                        "unlocked": project.unlocked,
                    }
                    for project in self.completed_projects
                ],
                "active_projects": [
                    {
                        "name": project.name,
                        "description": project.description,
                        "required_points": project.required_points,
                        "progress": project.progress,
                        "priority": project.priority,
                        "completed": project.completed,
                        "unlocked": project.unlocked,
                    }
                    for project in self.active_projects
                ],
                "research_queue": [
                    {
                        "name": project.name,
                        "description": project.description,
                        "required_points": project.required_points,
                        "progress": project.progress,
                        "priority": project.priority,
                        "completed": project.completed,
                        "unlocked": project.unlocked,
                    }
                    for project in self.research_queue
                ],
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "ResearchManager":

        manager = cls()

        manager.enabled = data.get(
            "enabled",
            True,
        )

        manager.initialized = data.get(
            "initialized",
            False,
        )

        manager.tick_count = data.get(
            "tick_count",
            0,
        )

        manager.hour_count = data.get(
            "hour_count",
            0,
        )

        manager.day_count = data.get(
            "day_count",
            0,
        )

        manager.update_count = data.get(
            "update_count",
            0,
        )

        manager.error_count = data.get(
            "error_count",
            0,
        )

        manager.research_points = data.get(
            "research_points",
            0.0,
        )

        return manager

    # ========================================================
    # Utility
    # ========================================================

    def clear(
        self,
    ) -> None:

        self.research_queue.clear()

        self.active_projects.clear()

        self.completed_projects.clear()

        self.research_points = 0.0

    def __repr__(
        self,
    ) -> str:

        return (
            "ResearchManager("
            f"queued={len(self.research_queue)}, "
            f"active={len(self.active_projects)}, "
            f"completed={len(self.completed_projects)}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Research = ResearchManager
