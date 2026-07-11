"""
accidents.py

Canonical accident management system for Habryn.

Responsible for generating and managing accidents involving
astronauts, robots, vehicles and colony operations.

Produces Accident events.

Coordinates with

- EventManager
- EmergencyManager
- Scheduler
- ColonyModel
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from enum import Enum

from random import choice
from random import random

from typing import Any

from colony.agents.astronaut import Astronaut
from colony.agents.robot import Robot

from colony.events.base_event import (
    BaseEvent,
    EventSeverity,
)

from colony.systems.base_manager import BaseManager
from colony.systems.emergency_manager import (
    EmergencyManager,
)

from colony.events.event_manager import (
    EventManager,
)

# ============================================================
# Accident Types
# ============================================================


class AccidentType(Enum):

    FALL = "Fall"

    EVA_FAILURE = "EVA Failure"

    TOOL_FAILURE = "Tool Failure"

    VEHICLE_COLLISION = "Vehicle Collision"

    ELECTRICAL_FIRE = "Electrical Fire"

    EXPLOSION = "Explosion"

    RADIATION = "Radiation Exposure"

    STRUCTURAL_COLLAPSE = "Structural Collapse"

    EQUIPMENT_FAILURE = "Equipment Failure"

    DECOMPRESSION = "Rapid Decompression"

    DUST_EXPOSURE = "Dust Exposure"

    UNKNOWN = "Unknown"


# ============================================================
# Accident Severity
# ============================================================


class AccidentSeverity(Enum):

    MINOR = EventSeverity.LOW

    MODERATE = EventSeverity.MEDIUM

    MAJOR = EventSeverity.HIGH

    CRITICAL = EventSeverity.CRITICAL

ACCIDENT_DAMAGE = {

    AccidentSeverity.MINOR: 10.0,

    AccidentSeverity.MODERATE: 25.0,

    AccidentSeverity.MAJOR: 50.0,

    AccidentSeverity.CRITICAL: 100.0,

}    

# ============================================================
# Accident Event
# ============================================================


@dataclass
class Accident(
    BaseEvent,
):

    accident_type: AccidentType = AccidentType.UNKNOWN

    victim: Any | None = None

    damage: float = 0.0

    radiation: float = 0.0

    requires_medical_attention: bool = False

    requires_robotics: bool = False

    fatal: bool = False

    # ========================================================
    # Helpers
    # ========================================================

    @property
    def astronaut_accident(
        self,
    ) -> bool:

        return isinstance(

            self.victim,

            Astronaut,

        )

    @property
    def robot_accident(
        self,
    ) -> bool:

        return isinstance(

            self.victim,

            Robot,

        )

    @property
    def critical(
        self,
    ) -> bool:

        return self.severity == EventSeverity.CRITICAL
    
# ============================================================
# Accident Manager
# ============================================================


@dataclass
class AccidentManager(
    BaseManager,
):

    name: str = "Accident Manager"

    event_manager: EventManager | None = None

    emergency_manager: EmergencyManager | None = None

    astronauts: list[Astronaut] = field(
        default_factory=list,
    )

    robots: list[Robot] = field(
        default_factory=list,
    )

    accidents: list[Accident] = field(
        default_factory=list,
    )

    accident_rate: float = 0.003

    total_accidents: int = 0

    resolved_accidents: int = 0

    # ========================================================
    # Manager Connections
    # ========================================================

    def connect_event_manager(
        self,
        manager: EventManager,
    ) -> None:

        self.event_manager = manager

    def connect_emergency_manager(
        self,
        manager: EmergencyManager,
    ) -> None:

        self.emergency_manager = manager

    @property
    def connected(
        self,
    ) -> bool:

        return (

            self.event_manager is not None

            and

            self.emergency_manager is not None

        )
    
    # ========================================================
    # Registration
    # ========================================================

    def register_astronaut(
        self,
        astronaut: Astronaut,
    ) -> None:

        if astronaut not in self.astronauts:

            self.astronauts.append(

                astronaut,

            )

    def unregister_astronaut(
        self,
        astronaut: Astronaut,
    ) -> None:

        if astronaut in self.astronauts:

            self.astronauts.remove(

                astronaut,

            )

    def register_robot(
        self,
        robot: Robot,
    ) -> None:

        if robot not in self.robots:

            self.robots.append(

                robot,

            )

    def unregister_robot(
        self,
        robot: Robot,
    ) -> None:

        if robot in self.robots:

            self.robots.remove(

                robot,

            )

    # ========================================================
    # Accident Generation
    # ========================================================

    def create_accident(
        self,
        victim: Astronaut | Robot,
    ) -> Accident:

        accident_type = choice(

            list(AccidentType),

        )

        severity = choice(

            list(AccidentSeverity),

        )

        damage = ACCIDENT_DAMAGE[
            severity
        ]

        radiation = (

            damage

            if accident_type == AccidentType.RADIATION

            else 0.0

        )

        accident = Accident(

            name=accident_type.value,

            description=(
                f"{accident_type.value} involving "
                f"{victim}"
            ),

            severity=severity.value,

            accident_type=accident_type,

            victim=victim,

            damage=damage,

            radiation=radiation,

            requires_medical_attention=isinstance(

                victim,

                Astronaut,

            ),

            requires_robotics=isinstance(

                victim,

                Robot,

            ),

            fatal=(

                severity

                == AccidentSeverity.CRITICAL

            ),

        )

        accident.activate(
            tick=self.tick_count,
        )

        self.accidents.append(

            accident,

        )

        self.total_accidents += 1

        return accident
    
    # ========================================================
    # Runtime
    # ========================================================

    def check_accidents(
        self,
    ) -> None:

        if not self.enabled:

            return

        for astronaut in self.astronauts:

            if random() < self.accident_rate:

                accident = self.create_accident(

                    astronaut,

                )

                if self.event_manager is not None:

                    self.event_manager.publish(

                        accident,

                    )

        for robot in self.robots:

            if random() < (

                self.accident_rate / 2.0

            ):

                accident = self.create_accident(

                    robot,

                )

                if self.event_manager is not None:

                    self.event_manager.publish(

                        accident,

                    )

    def step(
        self,
    ) -> None:

        super().step()

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

        self.check_accidents()

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

        finished = [

            accident

            for accident in self.accidents

            if accident.is_finished

        ]

        self.resolved_accidents = len(

            finished,

        )

    # ========================================================
    # Queries
    # ========================================================

    @property
    def active_accidents(
        self,
    ) -> list[Accident]:

        return [

            accident

            for accident in self.accidents

            if accident.is_active

        ]

    @property
    def finished_accidents(
        self,
    ) -> list[Accident]:

        return [

            accident

            for accident in self.accidents

            if accident.is_finished

        ]

    @property
    def accident_count(
        self,
    ) -> int:

        return len(

            self.accidents,

        )

    @property
    def astronaut_count(
        self,
    ) -> int:

        return len(

            self.astronauts,

        )

    @property
    def robot_count(
        self,
    ) -> int:

        return len(

            self.robots,

        )
    
    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict[str, Any]:

        data = super().statistics()

        data.update(

            {

                "astronauts":
                    self.astronaut_count,

                "robots":
                    self.robot_count,

                "accidents":
                    self.accident_count,

                "active_accidents":
                    len(

                        self.active_accidents,

                    ),

                "resolved_accidents":
                    self.resolved_accidents,

                "accident_rate":
                    self.accident_rate,

            }

        )

        return data

    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "AccidentManager("

            f"active={len(self.active_accidents)}, "

            f"total={self.accident_count}, "

            f"astronauts={self.astronaut_count}, "

            f"robots={self.robot_count}"

            ")"

        )


# ============================================================
# Canonical Alias
# ============================================================

Accidents = AccidentManager