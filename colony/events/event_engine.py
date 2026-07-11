"""
event_engine.py

Canonical Event Engine for Habryn.

Coordinates simulation lifecycle events.

Does NOT own events.

Does NOT create events.

Publishes simulation events to the EventManager.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

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
# Engine Event
# ============================================================


@dataclass
class EngineEvent(
    BaseEvent,
):

    source: str = ""

    payload: dict[str, Any] = field(
        default_factory=dict,
    )

# ============================================================
# Event Engine
# ============================================================


@dataclass
class EventEngine(
    BaseManager,
):

    name: str = "Event Engine"

    event_manager: EventManager | None = None

    published_events: int = 0

# ============================================================
# Connections
# ============================================================

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
    
# ============================================================
# Publishing
# ============================================================

    def publish(
        self,
        name: str,
        source: str,
        severity: EventSeverity = EventSeverity.LOW,
        description: str = "",
        payload: dict[str, Any] | None = None,
    ) -> EngineEvent:

        event = EngineEvent(

            name=name,

            description=description,

            severity=severity,

            source=source,

            payload=payload or {},

        )

        event.activate(

            tick=self.tick_count,

        )

        self.published_events += 1

        if self.event_manager is not None:

            self.event_manager.publish(

                event,

            )

        return event
    
# ============================================================
# Lifecycle Events
# ============================================================

    def tick_started(
        self,
    ) -> EngineEvent:

        return self.publish(

            name="Tick Started",

            source="Scheduler",

            payload={

                "tick": self.tick_count,

            },

        )

    def hour_started(
        self,
        hour: int,
    ) -> EngineEvent:

        return self.publish(

            name="Hour Started",

            source="Scheduler",

            payload={

                "hour": hour,

            },

        )

    def day_started(
        self,
        day: int,
    ) -> EngineEvent:

        return self.publish(

            name="Day Started",

            source="Scheduler",

            payload={

                "day": day,

            },

        )
    
    def month_started(
        self,
        month: int,
    ) -> EngineEvent:

        return self.publish(

            name="Month Started",

            source="Scheduler",

            payload={

                "month": month,

            },

        )

    def year_started(
        self,
        year: int,
    ) -> EngineEvent:

        return self.publish(

            name="Year Started",

            source="Scheduler",

            payload={

                "year": year,

            },

        )

    def sol_started(
        self,
        sol: int,
    ) -> EngineEvent:

        return self.publish(

            name="Sol Started",

            source="Scheduler",

            payload={

                "sol": sol,

            },

        )
    
    # ========================================================
    # Runtime
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
    ) -> dict[str, Any]:

        data = super().statistics()

        data.update(

            {

                "published_events":
                    self.published_events,

                "connected":
                    self.connected,

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

                "published_events":
                    self.published_events,

            }

        )

        return data
    
    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
    ) -> "EventEngine":

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

        manager.published_events = data.get(
            "published_events",
            0,
        )

        return manager
    
    # ========================================================
    # Utility
    # ========================================================

    def reset(
        self,
    ) -> None:

        super().reset()

        self.published_events = 0

    def __len__(
        self,
    ) -> int:

        return self.published_events

    def __bool__(
        self,
    ) -> bool:

        return self.connected
    
    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "EventEngine("

            f"published={self.published_events}, "

            f"connected={self.connected}"

            ")"

        )


# ============================================================
# Canonical Alias
# ============================================================

Engine = EventEngine