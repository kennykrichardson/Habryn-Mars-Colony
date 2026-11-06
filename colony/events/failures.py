"""
failures.py

Canonical infrastructure failure system.

Responsible for generating failures affecting
buildings and colony infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from enum import Enum

from random import choice
from random import random

from typing import Any

from colony.buildings.base_building import BaseBuilding

from colony.events.base_event import (
    BaseEvent,
    EventSeverity,
)

from colony.events.event_manager import EventManager

from colony.systems.base_manager import BaseManager
from colony.systems.emergency_manager import (
    EmergencyManager,
    EmergencySeverity,
)

# ============================================================
# Failure Types
# ============================================================


class FailureType(Enum):

    POWER = "Power Failure"

    OXYGEN = "Oxygen Failure"

    WATER = "Water Failure"

    STRUCTURAL = "Structural Failure"

    FIRE = "Fire"

    REACTOR = "Reactor Failure"

    COMMUNICATION = "Communication Failure"

    COMPUTER = "Computer Failure"

    LIFE_SUPPORT = "Life Support Failure"

    UNKNOWN = "Unknown"


# ============================================================
# Failure Severity
# ============================================================


class FailureSeverity(Enum):

    MINOR = EventSeverity.LOW

    MODERATE = EventSeverity.MEDIUM

    MAJOR = EventSeverity.HIGH

    CRITICAL = EventSeverity.CRITICAL


FAILURE_DAMAGE = {
    FailureSeverity.MINOR: 5.0,
    FailureSeverity.MODERATE: 20.0,
    FailureSeverity.MAJOR: 45.0,
    FailureSeverity.CRITICAL: 80.0,
}

# ============================================================
# Failure Event
# ============================================================


@dataclass
class Failure(
    BaseEvent,
):

    failure_type: FailureType = FailureType.UNKNOWN

    building: BaseBuilding | None = None

    damage: float = 0.0

    repair_time: int = 0

    power_loss: float = 0.0

    shutdown_required: bool = False

    catastrophic: bool = False


# ============================================================
# Failure Manager
# ============================================================


@dataclass
class FailureManager(
    BaseManager,
):

    name: str = "Failure Manager"

    event_manager: EventManager | None = None

    emergency_manager: EmergencyManager | None = None

    buildings: list[BaseBuilding] = field(
        default_factory=list,
    )

    failures: list[Failure] = field(
        default_factory=list,
    )

    failure_rate: float = 0.002

    total_failures: int = 0

    repaired_failures: int = 0

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

        return self.event_manager is not None and self.emergency_manager is not None

        # ========================================================

    # Registration
    # ========================================================

    def register_building(
        self,
        building: BaseBuilding,
    ) -> None:

        if building not in self.buildings:

            self.buildings.append(
                building,
            )

    def unregister_building(
        self,
        building: BaseBuilding,
    ) -> None:

        if building in self.buildings:

            self.buildings.remove(
                building,
            )

    # ========================================================
    # Failure Generation
    # ========================================================

    def create_failure(
        self,
        building: BaseBuilding,
    ) -> Failure:

        failure_type = choice(
            list(FailureType),
        )

        severity = choice(
            list(FailureSeverity),
        )

        damage = FAILURE_DAMAGE.get(
            severity,
            5.0,
        )
        shutdown_required = severity in (FailureSeverity.MAJOR, FailureSeverity.CRITICAL)

        failure = Failure(
            name=failure_type.value,
            description=(f"{failure_type.value} " f"at {building.name}"),
            severity=severity.value,
            failure_type=failure_type,
            building=building,
            damage=damage,
            repair_time=max(
                1,
                int(damage),
            ),
            power_loss=damage * 0.5,
            shutdown_required=shutdown_required,
            catastrophic=(severity == FailureSeverity.CRITICAL),
        )
        failure.event_id = f"failure-{self.total_failures + 1:06d}"

        failure.activate(
            tick=self.tick_count,
        )

        self.failures.append(
            failure,
        )

        self.total_failures += 1

        building.damage(damage)
        if shutdown_required:
            building.emergency_shutdown = True
            building.set_power(False)
        if self.emergency_manager is not None and shutdown_required:
            self.emergency_manager.report_emergency(
                title=f"{failure_type.value} at {building.name}",
                description="Infrastructure failure requires an engineer response.",
                severity=EmergencySeverity[severity.value.name], source=building, target=building,
                location=tuple(building.position))

        return failure

    # ========================================================
    # Runtime
    # ========================================================

    def check_failures(
        self,
    ) -> None:

        if not self.enabled:

            return

        for building in self.buildings:

            if random() >= self.failure_rate:

                continue

            failure = self.create_failure(
                building,
            )

            if self.event_manager is not None:

                self.event_manager.publish(
                    failure,
                )

    def step(
        self,
    ) -> None:

        super().step()

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

        self.check_failures()

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

        self.repaired_failures = len(
            [failure for failure in self.failures if failure.is_finished]
        )

    # ========================================================
    # Queries
    # ========================================================

    @property
    def active_failures(
        self,
    ) -> list[Failure]:

        return [failure for failure in self.failures if failure.is_active]

    @property
    def failure_count(
        self,
    ) -> int:

        return len(
            self.failures,
        )

    @property
    def building_count(
        self,
    ) -> int:

        return len(
            self.buildings,
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
                "buildings": self.building_count,
                "failures": self.failure_count,
                "active_failures": len(
                    self.active_failures,
                ),
                "repaired_failures": self.repaired_failures,
                "failure_rate": self.failure_rate,
            }
        )

        return data

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict[str, Any]:

        data = super().serialize()

        data.update(
            {
                "failure_rate": self.failure_rate,
                "total_failures": self.total_failures,
                "repaired_failures": self.repaired_failures,
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
    ) -> "FailureManager":

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

        manager.failure_rate = data.get(
            "failure_rate",
            0.002,
        )

        manager.total_failures = data.get(
            "total_failures",
            0,
        )

        manager.repaired_failures = data.get(
            "repaired_failures",
            0,
        )

        return manager

    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "FailureManager("
            f"active={len(self.active_failures)}, "
            f"total={self.failure_count}, "
            f"buildings={self.building_count}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Failures = FailureManager
