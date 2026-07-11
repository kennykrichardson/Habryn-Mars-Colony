"""
random_events.py

Canonical random event system.

Responsible for generating non-disaster colony events.

Examples

- Earth Supply Arrival
- Meteor Shower
- Scientific Discovery
- Visitor
- Solar Flare
- Equipment Shipment
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from enum import Enum

from random import choice
from random import random

from typing import Any

from colony.events.base_event import (
    BaseEvent,
    EventSeverity,
)

from colony.events.event_manager import (
    EventManager,
)

from colony.systems.base_manager import (
    BaseManager,
)

# ============================================================
# Random Event Types
# ============================================================


class RandomEventType(Enum):

    METEOR_SHOWER = "Meteor Shower"

    SOLAR_FLARE = "Solar Flare"

    SCIENTIFIC_DISCOVERY = "Scientific Discovery"

    EARTH_SUPPLY = "Earth Supply"

    COLONIST_CELEBRATION = "Colony Celebration"

    EQUIPMENT_SHIPMENT = "Equipment Shipment"

    COMMUNICATION_BOOST = "Communication Boost"

    VISITOR = "Visitor"

    UNKNOWN = "Unknown"


# ============================================================
# Random Event Severity
# ============================================================


class RandomEventSeverity(Enum):

    LOW = EventSeverity.LOW

    MEDIUM = EventSeverity.MEDIUM

    HIGH = EventSeverity.HIGH

    CRITICAL = EventSeverity.CRITICAL

# ============================================================
# Random Event
# ============================================================


@dataclass
class RandomEvent(
    BaseEvent,
):

    event_type: RandomEventType = RandomEventType.UNKNOWN

    probability: float = 0.0

    reward: float = 0.0

    penalty: float = 0.0

    global_event: bool = True

# ============================================================
# Random Event Manager
# ============================================================


@dataclass
class RandomEventManager(
    BaseManager,
):

    name: str = "Random Event Manager"

    event_manager: EventManager | None = None

    events: list[RandomEvent] = field(
        default_factory=list,
    )

    event_rate: float = 0.001

    total_events: int = 0

    completed_events: int = 0

    # ========================================================
    # Manager Connections
    # ========================================================

    def connect_event_manager(
        self,
        manager: EventManager,
    ) -> None:

        self.event_manager = manager

    @property
    def connected(
        self,
    ) -> bool:

        return self.event_manager is not None
    
    # ========================================================
    # Event Generation
    # ========================================================

    def create_event(
        self,
    ) -> RandomEvent:

        event_type = choice(

            list(RandomEventType),

        )

        severity = choice(

            list(RandomEventSeverity),

        )

        event = RandomEvent(

            name=event_type.value,

            description=event_type.value,

            severity=severity.value,

            event_type=event_type,

            probability=self.event_rate,

            reward=100.0,

            penalty=50.0,

            global_event=True,

        )

        event.activate(

            tick=self.tick_count,

        )

        self.events.append(

            event,

        )

        self.total_events += 1

        return event
    
    # ========================================================
    # Runtime
    # ========================================================

    def check_events(
        self,
    ) -> None:

        if not self.enabled:

            return

        if random() >= self.event_rate:

            return

        event = self.create_event()

        if self.event_manager is not None:

            self.event_manager.publish(

                event,

            )

    def step(
        self,
    ) -> None:

        super().step()

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

        self.check_events()

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

        self.completed_events = len(

            [

                event

                for event in self.events

                if event.is_finished

            ]

        )

    # ========================================================
    # Queries
    # ========================================================

    @property
    def active_events(
        self,
    ) -> list[RandomEvent]:

        return [

            event

            for event in self.events

            if event.is_active

        ]

    @property
    def event_count(
        self,
    ) -> int:

        return len(

            self.events,

        )

    @property
    def active_count(
        self,
    ) -> int:

        return len(

            self.active_events,

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

                "event_rate":
                    self.event_rate,

                "total_events":
                    self.total_events,

                "completed_events":
                    self.completed_events,

                "active_events":
                    self.active_count,

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

                "event_rate":
                    self.event_rate,

                "total_events":
                    self.total_events,

                "completed_events":
                    self.completed_events,

            }

        )

        return data
    
    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
    ) -> "RandomEventManager":

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

        manager.event_rate = data.get(
            "event_rate",
            0.001,
        )

        manager.total_events = data.get(
            "total_events",
            0,
        )

        manager.completed_events = data.get(
            "completed_events",
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

            "RandomEventManager("

            f"active={self.active_count}, "

            f"total={self.event_count}, "

            f"rate={self.event_rate}"

            ")"

        )


# ============================================================
# Canonical Alias
# ============================================================

RandomEvents = RandomEventManager