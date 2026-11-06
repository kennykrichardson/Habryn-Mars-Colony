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
from dataclasses import asdict
import random
from collections import deque
from dataclasses import replace
from enum import Enum
import json
from pathlib import Path

from colony.model import ColonyModel
from colony.scheduler import Scheduler
from colony.environment.mars_map import MarsMap
from colony.initialization import ColonyConfig, initialize_colony

# ============================================================
# Simulation
# ============================================================


@dataclass
class Simulation:

    config: ColonyConfig = field(default_factory=ColonyConfig)

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

        self.simulation_speed = self.config.simulation_speed
        self.scheduler.simulation_speed = self.simulation_speed
        if self.config.seed is not None:
            random.seed(self.config.seed)
        self.model = ColonyModel(scheduler=self.scheduler,
                                 mars_map=MarsMap(self.config.width, self.config.height),
                                 world_seed=self.config.seed or 0)
        self.model.social_manager.set_seed(self.config.seed)
        initialize_colony(self.model, self.config)

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
        self.scheduler.resume()

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

    def step_once(self) -> None:
        """Advance exactly one tick even while paused."""
        was_running, was_paused = self.scheduler.running, self.scheduler.paused
        self.scheduler.running, self.scheduler.paused = True, False
        self.scheduler.step()
        self.model.step()
        self.scheduler.running, self.scheduler.paused = was_running, was_paused

    def world_snapshot(self):
        return self.model.world_snapshot()

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
        self.simulation_speed = self.config.simulation_speed
        self.scheduler.simulation_speed = self.simulation_speed
        if self.config.seed is not None:
            random.seed(self.config.seed)
        self.model = ColonyModel(scheduler=self.scheduler,
                                 mars_map=MarsMap(self.config.width, self.config.height),
                                 world_seed=self.config.seed or 0)
        self.model.social_manager.set_seed(self.config.seed)
        initialize_colony(self.model, self.config)

    # ========================================================
    # Save / Load
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        return _json_safe({
            "schema_version": 2,
            "running": self.running,
            "paused": self.paused,
            "simulation_speed": self.simulation_speed,
            "config": asdict(self.config),
            "random_state": random.getstate(),
            "scheduler": self.scheduler.serialize(),
            "model": self.model.serialize(),
        })

    def save(self, path: str | Path) -> None:
        """Write a JSON save containing only authoritative simulation state."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.serialize(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Simulation":
        return cls.deserialize(json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Simulation":

        version = int(data.get("schema_version", 1))
        if version > 2:
            raise ValueError(f"Save schema {version} is newer than this Habryn build supports")
        if version < 1:
            raise ValueError(f"Unsupported save schema: {version}")

        saved_config = ColonyConfig(**data.get("config", {}))
        simulation = cls(config=replace(saved_config, populate=False))
        simulation.config = saved_config

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
        simulation.model.scheduler = simulation.scheduler
        simulation.model.connect_managers()
        if "model" in data:
            simulation.model.restore_serialized(data["model"])
        if data.get("random_state") is not None:
            random.setstate(_as_tuple(data["random_state"]))
        simulation.scheduler.running = simulation.running
        simulation.scheduler.paused = simulation.paused

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

            "simulation": {

                "running":
                    self.running,

                "paused":
                    self.paused,

                "speed":
                    self.simulation_speed,

            },

            "time": self.scheduler.statistics(),
            "colony": self.model.statistics(),
            "scheduler": self.scheduler.statistics(),
            "model": self.model.statistics(),

        }


    def debug_statistics(
        self,
    ) -> dict:

       return {

            "simulation": {

                "running":
                    self.running,

                "paused":
                    self.paused,

                "speed":
                    self.simulation_speed,

            },

            "time":

                self.scheduler.statistics(),

            "colony":

                self.model.debug_statistics(),

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

        self.scheduler.simulation_speed = self.simulation_speed

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

        return self.running and not self.paused

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
            f"Simulation(" f"Day {self.current_day}, " f"{self.current_hour:02}:00" f")"
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


def _as_tuple(value):
    """Convert JSON-decoded nested lists back to random.Random state tuples."""
    return tuple(_as_tuple(item) if isinstance(item, list) else item for item in value)


def _json_safe(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key.value if isinstance(key, Enum) else key): _json_safe(item)
                for key, item in value.items()}
    if isinstance(value, (tuple, list, deque)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    return value
