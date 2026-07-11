"""
task_manager.py

Part 1/4

Canonical Task Manager.

Owns every task in the colony.

Responsible for

- task creation
- task assignment
- task completion
- prioritization
- queues

Does NOT execute tasks.
Agents execute tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict

from colony.systems.base_manager import BaseManager
from colony.tasks.task import (
    BaseTask,
    TaskPriority,
    TaskStatus,
)


@dataclass
class TaskManager(BaseManager):

    name: str = "Task Manager"

    tasks: list[BaseTask] = field(default_factory=list)

    completed_tasks: list[BaseTask] = field(default_factory=list)

    failed_tasks: list[BaseTask] = field(default_factory=list)

    cancelled_tasks: list[BaseTask] = field(default_factory=list)

    assignments: dict[
        int,
        BaseTask,
    ] = field(default_factory=dict)

    # ========================================================
    # Registration
    # ========================================================

    def register_task(
        self,
        task: BaseTask,
    ) -> None:

        self.tasks.append(
            task,
        )

        self.sort_tasks()

    def remove_task(
        self,
        task: BaseTask,
    ) -> None:

        if task in self.tasks:

            self.tasks.remove(
                task,
            )

    # ========================================================
    # Creation
    # ========================================================

    def create_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = (TaskPriority.NORMAL),
        duration: int = 1,
    ) -> BaseTask:

        task = BaseTask(
            name=name,
            description=description,
            priority=priority,
            duration=duration,
        )

        self.register_task(
            task,
        )

        return task

    # ========================================================
    # Priority
    # ========================================================

    def sort_tasks(
        self,
    ) -> None:

        self.tasks.sort(
            key=lambda task: task.priority.value,
            reverse=True,
        )

        # ========================================================

    # Assignment
    # ========================================================

    def assign_task(
        self,
        agent,
        task: BaseTask,
    ) -> bool:

        if task.status != (TaskStatus.PENDING):

            return False

        task.assign(
            agent,
        )

        agent.assign_task(
            task,
        )

        self.assignments[agent.unique_id] = task

        return True

    def unassign_task(
        self,
        agent,
    ) -> None:

        task = self.assignments.pop(
            agent.unique_id,
            None,
        )

        if task is None:

            return

        task.unassign()

        agent.cancel_task()

    # ========================================================
    # Completion
    # ========================================================

    def complete_task(
        self,
        agent,
    ) -> None:

        task = self.assignments.pop(
            agent.unique_id,
            None,
        )

        if task is None:

            return

        task.complete()

        agent.complete_task()

        self.completed_tasks.append(
            task,
        )

        self.remove_task(
            task,
        )

    def fail_task(
        self,
        agent,
    ) -> None:

        task = self.assignments.pop(
            agent.unique_id,
            None,
        )

        if task is None:

            return

        task.fail()

        agent.cancel_task()

        self.failed_tasks.append(
            task,
        )

        self.remove_task(
            task,
        )

    def cancel_task(
        self,
        task: BaseTask,
    ) -> None:

        if task.status == (TaskStatus.COMPLETED):

            return

        task.cancel()

        self.cancelled_tasks.append(
            task,
        )

        self.remove_task(
            task,
        )

    # ========================================================
    # Queries
    # ========================================================

    def pending_tasks(
        self,
    ) -> list[BaseTask]:

        return [task for task in self.tasks if task.status == TaskStatus.PENDING]

    def active_tasks(
        self,
    ) -> list[BaseTask]:

        return [task for task in self.tasks if task.status == TaskStatus.IN_PROGRESS]

    def tasks_by_priority(
        self,
    ) -> dict[
        TaskPriority,
        list[BaseTask],
    ]:

        grouped = defaultdict(
            list,
        )

        for task in self.tasks:

            grouped[task.priority].append(
                task,
            )

        return dict(
            grouped,
        )

        # ========================================================

    # Update Loop
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        self.sort_tasks()

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

        self.sort_tasks()

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
                "total_tasks": len(
                    self.tasks,
                ),
                "pending_tasks": len(
                    self.pending_tasks(),
                ),
                "active_tasks": len(
                    self.active_tasks(),
                ),
                "completed_tasks": len(
                    self.completed_tasks,
                ),
                "failed_tasks": len(
                    self.failed_tasks,
                ),
                "cancelled_tasks": len(
                    self.cancelled_tasks,
                ),
                "assignments": len(
                    self.assignments,
                ),
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def clear_tasks(
        self,
    ) -> None:

        self.tasks.clear()

        self.completed_tasks.clear()

        self.failed_tasks.clear()

        self.cancelled_tasks.clear()

        self.assignments.clear()

    def __repr__(
        self,
    ) -> str:

        return (
            "TaskManager("
            f"tasks={len(self.tasks)}, "
            f"completed={len(self.completed_tasks)}, "
            f"active={len(self.assignments)}"
            ")"
        )

    # ============================================================
    # Serialization
    # ============================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data.update(
            {
                "tasks": [task.serialize() for task in self.tasks],
                "completed_tasks": [task.serialize() for task in self.completed_tasks],
                "failed_tasks": [task.serialize() for task in self.failed_tasks],
                "cancelled_tasks": [task.serialize() for task in self.cancelled_tasks],
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "TaskManager":

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

        manager.tasks = [
            BaseTask.deserialize(task)
            for task in data.get(
                "tasks",
                [],
            )
        ]

        manager.completed_tasks = [
            BaseTask.deserialize(task)
            for task in data.get(
                "completed_tasks",
                [],
            )
        ]

        manager.failed_tasks = [
            BaseTask.deserialize(task)
            for task in data.get(
                "failed_tasks",
                [],
            )
        ]

        manager.cancelled_tasks = [
            BaseTask.deserialize(task)
            for task in data.get(
                "cancelled_tasks",
                [],
            )
        ]

        return manager


# ============================================================
# Canonical Alias
# ============================================================

Tasks = TaskManager
