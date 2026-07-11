"""
scheduler.py

Canonical Habryn scheduler.

Owns simulation time.

Coordinates tick, hour, day, month,
year and Martian sol progression.

Does NOT execute simulation logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import Any


# ============================================================
# Scheduled Task
# ============================================================


@dataclass(slots=True)
class ScheduledTask:

    callback: Callable[..., Any]

    priority: int = 100

    enabled: bool = True

    name: str = ""

# ============================================================
# Scheduler
# ============================================================


@dataclass
class Scheduler:

    tasks: list[ScheduledTask] = field(
        default_factory=list,
    )

    running: bool = True

    paused: bool = False

    simulation_speed: float = 1.0

    tick: int = 0

    hour: int = 0

    day: int = 1

    month: int = 1

    year: int = 1

    sol: int = 1

    ticks_per_hour: int = 60

    hours_per_day: int = 24

    days_per_month: int = 30

    months_per_year: int = 12

    new_hour: bool = False

    new_day: bool = False

    new_month: bool = False

    new_year: bool = False

    new_sol: bool = False

    # ========================================================
    # Simulation Tick
    # ========================================================

    def step(
        self,
    ) -> None:

        if not self.running:

            return

        if self.paused:

            return

        self.new_hour = False

        self.new_day = False

        self.new_month = False

        self.new_year = False

        self.new_sol = False

        self.tick += 1

        self.update_time()

        for task in self.tasks:

            if not task.enabled:

                continue

            task.callback()

    # ========================================================
    # Time
    # ========================================================

    def update_time(
        self,
    ) -> None:

        if self.tick % self.ticks_per_hour != 0:

            return

        self.hour += 1

        self.new_hour = True

        self.update_day()

    # ========================================================
    # Calendar
    # ========================================================

    def update_day(
        self,
    ) -> None:

        if self.hour < self.hours_per_day:

            return

        self.hour = 0

        self.day += 1

        self.sol += 1

        self.new_day = True

        self.new_sol = True

        self.update_month()

    def update_month(
        self,
    ) -> None:

        if self.day <= self.days_per_month:

            return

        self.day = 1

        self.month += 1

        self.new_month = True

        self.update_year()

    def update_year(
        self,
    ) -> None:

        if self.month <= self.months_per_year:

            return

        self.month = 1

        self.year += 1

        self.new_year = True

    # ========================================================
    # Registration
    # ========================================================

    def register(
        self,
        callback: Callable[..., Any],
        priority: int = 100,
        name: str | None = None,
    ) -> None:

        self.tasks.append(

            ScheduledTask(

                callback=callback,

                priority=priority,

                name=name or callback.__name__,

            )

        )

        self.tasks.sort(

            key=lambda task: task.priority,

        )

    def unregister(
        self,
        callback: Callable[..., Any],
    ) -> None:

        self.tasks = [

            task

            for task in self.tasks

            if task.callback != callback

        ]

    def clear(
        self,
    ) -> None:

        self.tasks.clear()

    def enable(
        self,
        name: str,
    ) -> None:

        task = self.get_task(

            name,

        )

        if task is not None:

            task.enabled = True

    def disable(
        self,
        name: str,
    ) -> None:

        task = self.get_task(

            name,

        )

        if task is not None:

            task.enabled = False

    # ========================================================
    # Runtime Control
    # ========================================================

    def pause(
        self,
    ) -> None:

        self.paused = True

    def resume(
        self,
    ) -> None:

        self.paused = False

    def start(
        self,
    ) -> None:

        self.running = True

    def stop(
        self,
    ) -> None:

        self.running = False

    def reset(
        self,
    ) -> None:

        self.tick = 0

        self.hour = 0

        self.day = 1

        self.month = 1

        self.year = 1

        self.sol = 1

        self.running = True

        self.paused = False

        self.new_hour = False

        self.new_day = False

        self.new_month = False

        self.new_year = False

        self.new_sol = False

    # ========================================================
    # Properties
    # ========================================================

    @property
    def current_time(
        self,
    ) -> tuple[int, int]:

        return (

            self.hour,

            self.tick % self.ticks_per_hour,

        )

    @property
    def current_date(
        self,
    ) -> tuple[int, int, int]:

        return (

            self.day,

            self.month,

            self.year,

        )

    @property
    def total_days(
        self,
    ) -> int:

        return (

            (self.year - 1)

            * self.months_per_year

            * self.days_per_month

            +

            (self.month - 1)

            * self.days_per_month

            +

            self.day

        )
    
    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        return {

            "running":
                self.running,

            "paused":
                self.paused,

            "simulation_speed":
                self.simulation_speed,

            "tick":
                self.tick,

            "hour":
                self.hour,

            "day":
                self.day,

            "month":
                self.month,

            "year":
                self.year,

            "sol":
                self.sol,

            "task_count":
                len(

                    self.tasks,

                ),

            "new_hour":
                self.new_hour,

            "new_day":
                self.new_day,

            "new_month":
                self.new_month,

            "new_year":
                self.new_year,

            "new_sol":
                self.new_sol,

        }
    
    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        return {

            "running":
                self.running,

            "paused":
                self.paused,

            "simulation_speed":
                self.simulation_speed,

            "tick":
                self.tick,

            "hour":
                self.hour,

            "day":
                self.day,

            "month":
                self.month,

            "year":
                self.year,

            "sol":
                self.sol,

            "tasks": [

                {

                    "name":
                        task.name,

                    "priority":
                        task.priority,

                    "enabled":
                        task.enabled,

                }

                for task in self.tasks

            ],

        }

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Scheduler":

        scheduler = cls()

        scheduler.running = data.get(

            "running",

            True,

        )

        scheduler.paused = data.get(

            "paused",

            False,

        )

        scheduler.simulation_speed = data.get(

            "simulation_speed",

            1.0,

        )

        scheduler.tick = data.get(

            "tick",

            0,

        )

        scheduler.hour = data.get(

            "hour",

            0,

        )

        scheduler.day = data.get(

            "day",

            1,

        )

        scheduler.month = data.get(

            "month",

            1,

        )

        scheduler.year = data.get(

            "year",

            1,

        )

        scheduler.sol = data.get(

            "sol",

            1,

        )

        return scheduler
    
    # ========================================================
    # Utility
    # ========================================================

    def __len__(
        self,
    ) -> int:

        return len(

            self.tasks,

        )

    def __iter__(
        self,
    ):

        return iter(

            self.tasks,

        )

    def task_names(
        self,
    ) -> list[str]:

        return [

            task.name

            for task in self.tasks

        ]

    def get_task(
        self,
        name: str,
    ) -> ScheduledTask | None:

        for task in self.tasks:

            if task.name == name:

                return task

        return None

    def task_enabled(
        self,
        name: str,
    ) -> bool:

        task = self.get_task(

            name,

        )

        if task is None:

            return False

        return task.enabled
    
    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "Scheduler("

            f"tick={self.tick}, "

            f"time={self.hour:02d}:"

            f"{self.tick % self.ticks_per_hour:02d}, "

            f"day={self.day}, "

            f"month={self.month}, "

            f"year={self.year}, "

            f"tasks={len(self.tasks)}, "

            f"running={self.running}"

            ")"

        )


# ============================================================
# Canonical Alias
# ============================================================

SimulationScheduler = Scheduler