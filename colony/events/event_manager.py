"""
event_manager.py

Canonical Event Manager for Habryn.

Central dispatcher for every simulation event.

Owns

- active events
- archived events
- event history
- event dispatch
- subscriptions

Does NOT create events.

Specialized managers create events.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from collections import defaultdict

from typing import Callable
from typing import Any
from typing import TypeVar

from colony.events.base_event import (
    BaseEvent,
)

from colony.systems.base_manager import BaseManager

EventT = TypeVar(
    "EventT",
    bound=BaseEvent,
)

# ============================================================
# Event Manager
# ============================================================


@dataclass
class EventManager(
    BaseManager,
):

    name: str = "Event Manager"

    active_events: list[BaseEvent] = field(
        default_factory=list,
    )

    archived_events: list[BaseEvent] = field(
        default_factory=list,
    )

    subscribers: dict[
        type,
        list[Callable[[BaseEvent], None]]
    ] = field(

        default_factory=lambda:

        defaultdict(list)

    )

    dispatched_events: int = 0

    resolved_events: int = 0

    # ========================================================
    # Registration
    # ========================================================

    def publish(
        self,
        event: BaseEvent,
    ) -> None:

        if event in self.active_events:

            return

        self.active_events.append(

            event,

        )

        self.dispatched_events += 1

        self.dispatch(

            event,

        )

    def remove(
        self,
        event: BaseEvent,
    ) -> None:

        if event in self.active_events:

            self.active_events.remove(

                event,

            )

    # ========================================================
    # Subscribers
    # ========================================================

    def subscribe(
        self,
        event_type: type,
        callback: Callable[
            [BaseEvent],
            None,
        ],
    ) -> None:

        self.subscribers[
            event_type
        ].append(

            callback,

        )

    def unsubscribe(
        self,
        event_type: type,
        callback: Callable,
    ) -> None:

        if event_type not in self.subscribers:

            return

        callbacks = self.subscribers[
            event_type
        ]

        if callback in callbacks:

            callbacks.remove(

                callback,

            )

    # ========================================================
    # Dispatch
    # ========================================================

    def dispatch(
        self,
        event: BaseEvent,
    ) -> None:

        for event_type, callbacks in self.subscribers.items():

            if not isinstance(

                event,

                event_type,

            ):

                continue

            for callback in callbacks:

                callback(

                    event,

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

        self.cleanup()

    # ========================================================
    # Cleanup
    # ========================================================

    def cleanup(
        self,
    ) -> None:

        finished = [

            event

            for event in self.active_events

            if event.is_finished

        ]

        for event in finished:

            self.archive(

                event,

            )

    def archive(
        self,
        event: BaseEvent,
    ) -> None:

        if event in self.active_events:

            self.active_events.remove(

                event,

            )

        if event not in self.archived_events:

            self.archived_events.append(

                event,

            )

            self.resolved_events += 1

    # ========================================================
    # Queries
    # ========================================================

    @property
    def active_count(
        self,
    ) -> int:

        return len(

            self.active_events,

        )

    @property
    def archived_count(
        self,
    ) -> int:

        return len(

            self.archived_events,

        )

    @property
    def total_events(
        self,
    ) -> int:

        return (

            self.active_count

            +

            self.archived_count

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

                "active_events":
                    self.active_count,

                "archived_events":
                    self.archived_count,

                "total_events":
                    self.total_events,

                "dispatched_events":
                    self.dispatched_events,

                "resolved_events":
                    self.resolved_events,

                "subscriber_types":
                    len(

                        self.subscribers,

                    ),

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

                "active_events":

                    [

                        event.serialize()

                        for event in self.active_events

                    ],

                "archived_events":

                    [

                        event.serialize()

                        for event in self.archived_events

                    ],

                "dispatched_events":

                    self.dispatched_events,

                "resolved_events":

                    self.resolved_events,

            }

        )

        return data
        
    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
    ) -> "EventManager":

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

        manager.dispatched_events = data.get(

            "dispatched_events",

            0,

        )

        manager.resolved_events = data.get(

            "resolved_events",

            0,

        )

        return manager
    
    # ========================================================
    # Utility
    # ========================================================

    def clear(
        self,
    ) -> None:

        self.active_events.clear()

        self.archived_events.clear()

        self.subscribers.clear()

        self.dispatched_events = 0

        self.resolved_events = 0

    def reset(
        self,
    ) -> None:

        super().reset()

        self.clear()

    def active_of_type(
        self,
        event_type: type[BaseEvent],
    ) -> list[BaseEvent]:

        return [

            event

            for event in self.active_events

            if isinstance(

                event,

                event_type,

            )

        ]

    def archived_of_type(
        self,
        event_type: type[BaseEvent],
    ) -> list[BaseEvent]:

        return [

            event

            for event in self.archived_events

            if isinstance(

                event,

                event_type,

            )

        ]
    
    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "EventManager("

            f"active={self.active_count}, "

            f"archived={self.archived_count}, "

            f"total={self.total_events}"

            ")"

        )


# ============================================================
# Canonical Alias
# ============================================================

Events = EventManager