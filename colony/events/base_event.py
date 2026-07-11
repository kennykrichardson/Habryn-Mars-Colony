"""
base_event.py

Part 1/3

Canonical base class for every event in Habryn.

Inheritance

BaseEvent
├── RandomEvent
├── Accident
├── Failure
├── DustStorm
├── MeteorImpact
├── SolarFlare
├── Fire
├── RadiationLeak
├── HullBreach
└── DiseaseOutbreak

Events represent something that occurs in the simulation.

They do not execute colony logic themselves.
Managers decide what to do with them.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any
from uuid import uuid4

# ============================================================
# Event Severity
# ============================================================


class EventSeverity(Enum):

    INFO = "Info"

    LOW = "Low"

    MEDIUM = "Medium"

    HIGH = "High"

    CRITICAL = "Critical"


# ============================================================
# Event State
# ============================================================


class EventState(Enum):

    PENDING = "Pending"

    ACTIVE = "Active"

    RESOLVED = "Resolved"

    FAILED = "Failed"

    CANCELLED = "Cancelled"


# ============================================================
# Base Event
# ============================================================


@dataclass
class BaseEvent:

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    name: str

    description: str

    severity: EventSeverity = EventSeverity.INFO

    # --------------------------------------------------------
    # Runtime
    # --------------------------------------------------------

    event_id: str = field(default_factory=lambda: str(uuid4()))

    state: EventState = EventState.PENDING

    active: bool = False

    resolved: bool = False

    failed: bool = False

    # --------------------------------------------------------
    # Timing
    # --------------------------------------------------------

    created_tick: int = 0

    activated_tick: int | None = None

    resolved_tick: int | None = None

    duration: int = 0

    # --------------------------------------------------------
    # Optional References
    # --------------------------------------------------------

    source: Any | None = None

    target: Any | None = None

    location: tuple[int, int] | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    # ========================================================
    # Lifecycle
    # ========================================================

    def activate(
        self,
        tick: int | None = None,
    ) -> None:

        self.active = True

        self.state = EventState.ACTIVE

        if tick is not None:

            self.activated_tick = tick

    def resolve(
        self,
        tick: int | None = None,
    ) -> None:

        self.active = False

        self.resolved = True

        self.state = EventState.RESOLVED

        if tick is not None:

            self.resolved_tick = tick

    def cancel(
        self,
    ) -> None:

        self.active = False

        self.state = EventState.CANCELLED

    def fail(
        self,
    ) -> None:

        self.failed = True

        self.active = False

        self.state = EventState.FAILED

    # ========================================================
    # Update
    # ========================================================

    def step(
        self,
    ) -> None:

        if not self.active:

            return

        self.duration += 1

    def hourly_update(
        self,
    ) -> None:

        self.step()

    def daily_update(
        self,
    ) -> None:

        pass

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
    # Helpers
    # ========================================================

    @property
    def is_active(
        self,
    ) -> bool:

        return self.state == EventState.ACTIVE

    @property
    def is_finished(
        self,
    ) -> bool:

        return self.state in (
            EventState.RESOLVED,
            EventState.CANCELLED,
            EventState.FAILED,
        )

    @property
    def age(
        self,
    ) -> int:

        return self.duration

    def restart(
        self,
    ) -> None:

        self.state = EventState.PENDING

        self.active = False

        self.resolved = False

        self.failed = False

        self.duration = 0

        self.activated_tick = None

        self.resolved_tick = None

    def copy(
        self,
    ) -> "BaseEvent":

        return self.deserialize(
            self.serialize(),
        )

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict[str, Any]:

        data = asdict(self)

        data["severity"] = self.severity.value

        data["state"] = self.state.value

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
    ) -> "BaseEvent":

        severity = EventSeverity(
            data.pop(
                "severity",
            ),
        )

        state = EventState(
            data.pop(
                "state",
            ),
        )

        event = cls(
            **data,
        )

        event.severity = severity

        event.state = state

        return event

        # ========================================================

    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict[str, Any]:

        return {
            "id": self.event_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "state": self.state.value,
            "active": self.active,
            "resolved": self.resolved,
            "failed": self.failed,
            "created_tick": self.created_tick,
            "activated_tick": self.activated_tick,
            "resolved_tick": self.resolved_tick,
            "duration": self.duration,
            "location": self.location,
            "source": (None if self.source is None else str(self.source)),
            "target": (None if self.target is None else str(self.target)),
        }

    # ========================================================
    # Utility
    # ========================================================

    def __hash__(
        self,
    ) -> int:

        return hash(
            self.event_id,
        )

    def __eq__(
        self,
        other: object,
    ) -> bool:

        if not isinstance(
            other,
            BaseEvent,
        ):

            return False

        return self.event_id == other.event_id

    def __repr__(
        self,
    ) -> str:

        return (
            "BaseEvent("
            f"name='{self.name}', "
            f"severity='{self.severity.value}', "
            f"state='{self.state.value}', "
            f"active={self.active}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Event = BaseEvent
