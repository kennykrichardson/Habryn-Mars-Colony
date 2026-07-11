"""
logistics_manager.py

Part 1/4

Canonical Logistics Manager.

Responsible for resource movement throughout the colony.

Owns

- building registry
- transport requests
- delivery queue
- robot assignments
- storage routing

Does NOT move resources itself.

Agents and robots perform deliveries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import Any

from colony.systems.base_manager import BaseManager


@dataclass(slots=True)
class TransportRequest:

    resource: str

    amount: float

    source: Any

    destination: Any

    priority: int = 1

    assigned_robot: Any | None = None

    completed: bool = False


# ============================================================
# Logistics Manager
# ============================================================


@dataclass
class LogisticsManager(BaseManager):

    name: str = "Logistics Manager"

    buildings: dict[int, Any] = field(default_factory=dict)

    robots: dict[int, Any] = field(default_factory=dict)

    delivery_queue: deque[TransportRequest] = field(default_factory=deque)

    completed_deliveries: int = 0

    failed_deliveries: int = 0

    # ========================================================
    # Registration
    # ========================================================

    def register_building(
        self,
        building: Any,
    ) -> None:

        self.buildings[building.building_id] = building

    def register_robot(
        self,
        robot: Any,
    ) -> None:

        self.robots[robot.unique_id] = robot

    # ========================================================
    # Requests
    # ========================================================

    def create_request(
        self,
        resource: str,
        amount: float,
        source: Any,
        destination: Any,
        priority: int = 1,
    ) -> TransportRequest:

        request = TransportRequest(
            resource=resource,
            amount=amount,
            source=source,
            destination=destination,
            priority=priority,
        )

        self.delivery_queue.append(
            request,
        )

        return request

        # ========================================================

    # Assignment
    # ========================================================

    def assign_robot(
        self,
        robot: Any,
        request: TransportRequest,
    ) -> bool:

        if request.assigned_robot is not None:

            return False

        request.assigned_robot = robot

        return True

    def next_request(
        self,
    ) -> TransportRequest | None:

        if not self.delivery_queue:

            return None

        highest = max(
            self.delivery_queue,
            key=lambda request: request.priority,
        )

        self.delivery_queue.remove(
            highest,
        )

        return highest

    # ========================================================
    # Completion
    # ========================================================

    def complete_request(
        self,
        request: TransportRequest,
    ) -> None:

        request.completed = True

        self.completed_deliveries += 1

    def fail_request(
        self,
        request: TransportRequest,
    ) -> None:

        self.failed_deliveries += 1

    # ========================================================
    # Queries
    # ========================================================

    def pending_requests(
        self,
    ) -> list[TransportRequest]:

        return [request for request in self.delivery_queue if not request.completed]

    def requests_for_robot(
        self,
        robot: Any,
    ) -> list[TransportRequest]:

        return [
            request
            for request in self.delivery_queue
            if request.assigned_robot == robot
        ]

    def requests_for_resource(
        self,
        resource: str,
    ) -> list[TransportRequest]:

        return [
            request for request in self.delivery_queue if request.resource == resource
        ]

        # ========================================================

    # Update Loop
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
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "registered_buildings": len(
                    self.buildings,
                ),
                "registered_robots": len(
                    self.robots,
                ),
                "pending_requests": len(
                    self.pending_requests(),
                ),
                "completed_deliveries": self.completed_deliveries,
                "failed_deliveries": self.failed_deliveries,
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def clear_requests(
        self,
    ) -> None:

        self.delivery_queue.clear()

    def clear(
        self,
    ) -> None:

        self.buildings.clear()

        self.robots.clear()

        self.delivery_queue.clear()

        self.completed_deliveries = 0

        self.failed_deliveries = 0

    def __repr__(
        self,
    ) -> str:

        return (
            "LogisticsManager("
            f"requests={len(self.delivery_queue)}, "
            f"robots={len(self.robots)}, "
            f"completed={self.completed_deliveries}"
            ")"
        )

        # ========================================================

    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data.update(
            {
                "completed_deliveries": self.completed_deliveries,
                "failed_deliveries": self.failed_deliveries,
                "delivery_queue": [
                    {
                        "resource": request.resource,
                        "amount": request.amount,
                        "priority": request.priority,
                        "completed": request.completed,
                    }
                    for request in self.delivery_queue
                ],
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "LogisticsManager":

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

        manager.completed_deliveries = data.get(
            "completed_deliveries",
            0,
        )

        manager.failed_deliveries = data.get(
            "failed_deliveries",
            0,
        )

        for request_data in data.get(
            "delivery_queue",
            [],
        ):

            manager.delivery_queue.append(
                TransportRequest(
                    resource=request_data["resource"],
                    amount=request_data["amount"],
                    source=None,
                    destination=None,
                    priority=request_data.get(
                        "priority",
                        1,
                    ),
                    completed=request_data.get(
                        "completed",
                        False,
                    ),
                )
            )

        return manager


# ============================================================
# Canonical Alias
# ============================================================

Logistics = LogisticsManager
