"""
simulation.py

Canonical Habryn Simulation Engine.

Owns the simulation lifecycle.

Coordinates

- Scheduler
- Colony Model
- Renderer
- Dashboard

Provides

- Run
- Stop
- Pause
- Resume
- Reset
- Save
- Load

Acts as the application's runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.model import ColonyModel
from colony.scheduler import Scheduler

# ============================================================
# Simulation
# ============================================================


@dataclass
class Simulation:

    model: ColonyModel = field(

        init=False,

    )

    scheduler: Scheduler = field(

        default_factory=Scheduler,

    )

    running: bool = False

    paused: bool = False

    simulation_speed: float = 1.0

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        self.model = ColonyModel(

            scheduler=self.scheduler,

        )

        self.running = False

        self.paused = False

    # ========================================================
    # Runtime Control
    # ========================================================

    def start(
        self,
    ) -> None:

        self.running = True

        self.paused = False

        self.scheduler.start()

    def stop(
        self,
    ) -> None:

        self.running = False

        self.scheduler.stop()

    def pause(
        self,
    ) -> None:

        self.paused = True

        self.scheduler.pause()

    def resume(
        self,
    ) -> None:

        self.paused = False

        self.scheduler.resume()

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        if not self.running:

            return

        if self.paused:

            return

        self.scheduler.step()

        self.model.step()

    # ========================================================
    # Simulation Loop
    # ========================================================

    def run(
        self,
    ) -> None:

        self.start()

        while self.running:

            self.step()

    # ========================================================
    # Reset
    # ========================================================

    def reset(
        self,
    ) -> None:

        self.stop()

        self.scheduler.reset()

        self.model.reset()

    # ========================================================
    # Save / Load
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

            "scheduler":
                self.scheduler.serialize(),

            "model":
                self.model.serialize(),

        }

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Simulation":

        simulation = cls()

        simulation.running = data.get(

            "running",

            False,

        )

        simulation.paused = data.get(

            "paused",

            False,

        )

        simulation.simulation_speed = data.get(

            "simulation_speed",

            1.0,

        )

        simulation.scheduler = Scheduler.deserialize(

            data.get(

                "scheduler",

                {},

            )

        )

        return simulation
    
    # ========================================================
    # Queries
    # ========================================================

    @property
    def initialized(
        self,
    ) -> bool:

        return self.model.initialized

    @property
    def current_tick(
        self,
    ) -> int:

        return self.scheduler.tick

    @property
    def current_hour(
        self,
    ) -> int:

        return self.scheduler.hour

    @property
    def current_day(
        self,
    ) -> int:

        return self.scheduler.day

    @property
    def current_month(
        self,
    ) -> int:

        return self.scheduler.month

    @property
    def current_year(
        self,
    ) -> int:

        return self.scheduler.year
    
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

            "initialized":
                self.initialized,

            "scheduler":
                self.scheduler.statistics(),

            "model":
                self.model.statistics(),

        }
    
    # ========================================================
    # Speed
    # ========================================================

    def set_speed(
        self,
        speed: float,
    ) -> None:

        self.simulation_speed = max(

            0.1,

            speed,

        )

        self.scheduler.simulation_speed = (

            self.simulation_speed

        )

    def increase_speed(
        self,
        amount: float = 0.25,
    ) -> None:

        self.set_speed(

            self.simulation_speed + amount,

        )

    def decrease_speed(
        self,
        amount: float = 0.25,
    ) -> None:

        self.set_speed(

            self.simulation_speed - amount,

        )

    # ========================================================
    # Utility
    # ========================================================

    def is_running(
        self,
    ) -> bool:

        return (

            self.running

            and

            not self.paused

        )

    def is_paused(
        self,
    ) -> bool:

        return self.paused

    def toggle_pause(
        self,
    ) -> None:

        if self.paused:

            self.resume()

        else:

            self.pause()

    # ========================================================
    # Representation
    # ========================================================

    def __str__(
        self,
    ) -> str:

        return (

            f"Simulation("

            f"Day {self.current_day}, "

            f"{self.current_hour:02}:00"

            f")"

        )

    def __repr__(
        self,
    ) -> str:

        return (

            "Simulation("

            f"running={self.running}, "

            f"paused={self.paused}, "

            f"speed={self.simulation_speed:.2f}, "

            f"tick={self.current_tick}"

            ")"

        )
    
    # ========================================================
    # Context Manager
    # ========================================================

    def __enter__(
        self,
    ) -> "Simulation":

        self.start()

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:

        self.stop()

# ============================================================
# Canonical Alias
# ============================================================

SimulationEngine = Simulation