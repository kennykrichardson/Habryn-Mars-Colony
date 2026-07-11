"""
task.py

Part 1/3

Canonical task system for Habryn.

Every piece of work performed in the colony should inherit
from BaseTask or use it directly.

Examples

Repair Solar Array
Harvest Greenhouse
Mine Ice
Transport Oxygen
Research Fusion
Construct Habitat
Treat Patient
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

# ============================================================
# Task Priority
# ============================================================


class TaskPriority(Enum):

    LOW = 1

    NORMAL = 2

    HIGH = 3

    URGENT = 4

    CRITICAL = 5


# ============================================================
# Task Status
# ============================================================


class TaskStatus(Enum):

    PENDING = "Pending"

    ASSIGNED = "Assigned"

    IN_PROGRESS = "In Progress"

    COMPLETED = "Completed"

    FAILED = "Failed"

    CANCELLED = "Cancelled"


# ============================================================
# Base Task
# ============================================================


@dataclass
class BaseTask:

    name: str

    description: str = ""

    priority: TaskPriority = TaskPriority.NORMAL

    duration: int = 1

    task_id: str = field(default_factory=lambda: str(uuid4()))

    status: TaskStatus = TaskStatus.PENDING

    assigned_agent: Any | None = None

    target: Any | None = None

    location: tuple[int, int] | None = None

    progress: float = 0.0

    required_skills: dict[str, int] = field(default_factory=dict)

    required_resources: dict[str, float] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)

    # ========================================================
    # Assignment
    # ========================================================

    def assign(
        self,
        agent: Any,
    ) -> None:

        self.assigned_agent = agent

        self.status = TaskStatus.ASSIGNED

    def unassign(
        self,
    ) -> None:

        self.assigned_agent = None

        self.status = TaskStatus.PENDING

    # ========================================================
    # Execution
    # ========================================================

    def start(
        self,
    ) -> None:

        self.status = TaskStatus.IN_PROGRESS

    def advance(
        self,
        amount: float,
    ) -> None:

        if self.status != TaskStatus.IN_PROGRESS:
            return

        self.progress = min(
            100.0,
            self.progress + amount,
        )

        if self.progress >= 100.0:
            self.complete()

    def complete(
        self,
    ) -> None:

        self.progress = 100.0

        self.status = TaskStatus.COMPLETED

    def fail(
        self,
    ) -> None:

        self.status = TaskStatus.FAILED

    def cancel(
        self,
    ) -> None:

        self.status = TaskStatus.CANCELLED

    def reset(
        self,
    ) -> None:

        self.progress = 0.0

        self.assigned_agent = None

        self.status = TaskStatus.PENDING

    # ========================================================
    # Queries
    # ========================================================

    @property
    def assigned(
        self,
    ) -> bool:

        return self.assigned_agent is not None

    @property
    def completed(
        self,
    ) -> bool:

        return self.status == TaskStatus.COMPLETED

    @property
    def active(
        self,
    ) -> bool:

        return self.status == TaskStatus.IN_PROGRESS

    # ========================================================
    # Metadata
    # ========================================================

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.metadata[key] = value

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.metadata.get(
            key,
            default,
        )

    def clear_metadata(
        self,
    ) -> None:

        self.metadata.clear()

        # ========================================================

    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict[str, Any]:

        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "duration": self.duration,
            "progress": self.progress,
            "location": self.location,
            "required_skills": dict(
                self.required_skills,
            ),
            "required_resources": dict(
                self.required_resources,
            ),
            "metadata": dict(
                self.metadata,
            ),
        }

    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
    ) -> "BaseTask":

        task = cls(
            name=data["name"],
            description=data.get(
                "description",
                "",
            ),
            duration=data.get(
                "duration",
                1,
            ),
        )

        task.task_id = data.get(
            "task_id",
            task.task_id,
        )

        task.priority = TaskPriority(
            data.get(
                "priority",
                TaskPriority.NORMAL.value,
            )
        )

        task.status = TaskStatus(
            data.get(
                "status",
                TaskStatus.PENDING.value,
            )
        )

        task.progress = data.get(
            "progress",
            0.0,
        )

        task.location = data.get(
            "location",
        )

        task.required_skills = dict(
            data.get(
                "required_skills",
                {},
            )
        )

        task.required_resources = dict(
            data.get(
                "required_resources",
                {},
            )
        )

        task.metadata = dict(
            data.get(
                "metadata",
                {},
            )
        )

        return task

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict[str, Any]:

        return {
            "id": self.task_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.name,
            "status": self.status.value,
            "duration": self.duration,
            "progress": round(
                self.progress,
                2,
            ),
            "assigned": self.assigned,
            "assigned_agent": (
                None if self.assigned_agent is None else str(self.assigned_agent)
            ),
            "location": self.location,
            "required_skills": dict(
                self.required_skills,
            ),
            "required_resources": dict(
                self.required_resources,
            ),
        }

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "BaseTask("
            f"name='{self.name}', "
            f"priority='{self.priority.name}', "
            f"status='{self.status.value}', "
            f"progress={self.progress:.1f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Task = BaseTask
