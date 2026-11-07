"""
construction_manager.py

Part 1/4

Canonical Construction Manager.

Responsible for every construction project in the colony.

Owns

- construction queue
- active projects
- completed projects
- builder assignments

Does NOT construct buildings.

Engineers and BuilderBots perform construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import Any

from colony.systems.base_manager import BaseManager
from colony.systems.power_grid import PowerGrid
from colony.systems.population_manager import PopulationManager
from colony.systems.resource_manager import ResourceManager

# ============================================================
# Construction Project
# ============================================================


@dataclass(slots=True)
class ConstructionProject:

    building_name: str

    position: tuple[int, int]

    required_resources: dict[
        str,
        float,
    ]

    progress: float = 0.0

    priority: int = 1

    assigned_agent: Any | None = None

    completed: bool = False

    task_id: str | None = None

    footprint: tuple[int, int] = (3, 3)


# ============================================================
# Construction Manager
# ============================================================


@dataclass
class ConstructionManager(BaseManager):

    name: str = "Construction Manager"

    construction_queue: deque[ConstructionProject] = field(default_factory=deque)

    active_projects: list[ConstructionProject] = field(default_factory=list)

    completed_projects: int = 0

    cancelled_projects: int = 0

    # ========================================================
    # Connected Managers
    # ========================================================

    resource_manager: ResourceManager | None = None

    power_grid: PowerGrid | None = None

    population_manager: PopulationManager | None = None

    # ========================================================
    # Manager Connections
    # ========================================================

    def connect_resource_manager(
        self,
        manager: ResourceManager,
    ) -> None:

        self.resource_manager = manager

    def connect_power_grid(
        self,
        manager: PowerGrid,
    ) -> None:

        self.power_grid = manager

    def connect_population_manager(
        self,
        manager: PopulationManager,
    ) -> None:

        self.population_manager = manager

    @property
    def managers_connected(
        self,
    ) -> bool:

        return (
            self.resource_manager is not None
            and self.power_grid is not None
            and self.population_manager is not None
        )

    # ========================================================
    # Projects
    # ========================================================

    def create_project(
        self,
        building_name: str,
        position: tuple[int, int],
        required_resources: dict[
            str,
            float,
        ],
        priority: int = 1,
    ) -> ConstructionProject:
        project = ConstructionProject(
            building_name=building_name,
            position=position,
            required_resources=required_resources,
            priority=priority,
        )

        self.construction_queue.append(
            project,
        )

        return project

    def can_begin_project(
        self,
        project: ConstructionProject,
    ) -> bool:

        if not self.managers_connected:

            return False

        assert self.resource_manager is not None
        assert self.population_manager is not None

        # Resource exists?

        for resource_name in project.required_resources:

            if not self.resource_manager.has_resource(
                resource_name,
            ):

                return False

        # Enough resources?

        for resource_name, amount in project.required_resources.items():

            if (
                self.resource_manager.amount(
                    resource_name,
                )
                < amount
            ):

                return False

        # Workers available?

        if self.population_manager.available_workers <= 0:

            return False

        return True

    # ========================================================
    # Assignment
    # ========================================================

    def assign_project(
        self,
        agent: Any,
        project: ConstructionProject,
    ) -> bool:

        if project.assigned_agent is not None:

            return False

        if not self.can_begin_project(
            project,
        ):

            return False

        assert self.resource_manager is not None
        assert self.population_manager is not None

        project.assigned_agent = agent

        for resource_name, amount in project.required_resources.items():

            self.resource_manager.consume(
                resource_name,
                amount,
            )

        self.population_manager.employ(
            1,
        )

        self.active_projects.append(
            project,
        )

        if project in self.construction_queue:

            self.construction_queue.remove(
                project,
            )

        return True

    # ========================================================
    # Completion
    # ========================================================

    def complete_project(
        self,
        project: ConstructionProject,
    ) -> None:

        project.progress = 100.0

        project.completed = True

        if project in self.active_projects:

            self.active_projects.remove(
                project,
            )

        manager = self.population_manager

        if manager is not None:

            manager.dismiss(
                1,
            )

        self.completed_projects += 1

    def cancel_project(
        self,
        project: ConstructionProject,
    ) -> None:

        if project in self.active_projects:

            self.active_projects.remove(
                project,
            )

        elif project in self.construction_queue:

            self.construction_queue.remove(
                project,
            )

        self.cancelled_projects += 1

        if project.assigned_agent is not None:

            manager = self.population_manager

            if manager is not None:

                manager.dismiss(
                    1,
                )

    # ========================================================
    # Queries
    # ========================================================

    def next_project(
        self,
    ) -> ConstructionProject | None:

        if not self.construction_queue:

            return None

        project = max(
            self.construction_queue,
            key=lambda p: p.priority,
        )

        self.construction_queue.remove(
            project,
        )

        self.active_projects.append(
            project,
        )

        return project

    def pending_projects(
        self,
    ) -> list[ConstructionProject]:

        return list(
            self.construction_queue,
        )

    def projects_for_agent(
        self,
        agent: Any,
    ) -> list[ConstructionProject]:

        return [
            project
            for project in self.active_projects
            if project.assigned_agent == agent
        ]

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
                "pending_projects": len(
                    self.construction_queue,
                ),
                "active_projects": len(
                    self.active_projects,
                ),
                "completed_projects": self.completed_projects,
                "cancelled_projects": self.cancelled_projects,
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def clear(
        self,
    ) -> None:

        self.construction_queue.clear()

        self.active_projects.clear()

        self.completed_projects = 0

        self.cancelled_projects = 0

    def __repr__(
        self,
    ) -> str:

        return (
            "ConstructionManager("
            f"pending={len(self.construction_queue)}, "
            f"active={len(self.active_projects)}, "
            f"completed={self.completed_projects}"
            ")"
        )

        # ========================================================

    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data.update(
            {
                "completed_projects": self.completed_projects,
                "cancelled_projects": self.cancelled_projects,
                "active_projects": [
                    {
                        "building_name": project.building_name,
                        "position": project.position,
                        "required_resources": dict(project.required_resources),
                        "progress": project.progress,
                        "priority": project.priority,
                        "completed": project.completed,
                    }
                    for project in self.active_projects
                ],
                "construction_queue": [
                    {
                        "building_name": project.building_name,
                        "position": project.position,
                        "required_resources": dict(project.required_resources),
                        "progress": project.progress,
                        "priority": project.priority,
                        "completed": project.completed,
                    }
                    for project in self.construction_queue
                ],
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "ConstructionManager":

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

        manager.completed_projects = data.get(
            "completed_projects",
            0,
        )

        manager.cancelled_projects = data.get(
            "cancelled_projects",
            0,
        )

        return manager


# ============================================================
# Canonical Alias
# ============================================================

Construction = ConstructionManager
