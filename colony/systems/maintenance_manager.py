"""
maintenance_manager.py

Part 1/4

Canonical Maintenance Manager.

Responsible for keeping colony infrastructure operational.

Owns

- building registry
- maintenance queue
- repair requests
- inspection scheduling

Does NOT perform repairs.

Engineers and repair robots perform repairs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import Any

from colony.systems.base_manager import BaseManager

# ============================================================
# Maintenance Request
# ============================================================


@dataclass(slots=True)
class MaintenanceRequest:

    building: Any

    priority: int = 1

    repair_amount: float = 10.0

    assigned_agent: Any | None = None

    completed: bool = False


# ============================================================
# Maintenance Manager
# ============================================================


@dataclass
class MaintenanceManager(BaseManager):

    name: str = "Maintenance Manager"

    buildings: dict[int, Any] = field(default_factory=dict)

    maintenance_queue: deque[MaintenanceRequest] = field(default_factory=deque)

    completed_repairs: int = 0

    failed_repairs: int = 0

    inspections: int = 0

    # ========================================================
    # Registration
    # ========================================================

    def register_building(
        self,
        building: Any,
    ) -> None:

        self.buildings[building.building_id] = building

    def unregister_building(
        self,
        building: Any,
    ) -> None:

        self.buildings.pop(
            building.building_id,
            None,
        )

    # ========================================================
    # Requests
    # ========================================================

    def request_maintenance(
        self,
        building: Any,
        priority: int = 1,
        repair_amount: float = 10.0,
    ) -> MaintenanceRequest:

        for existing in self.maintenance_queue:
            if existing.building is building and not existing.completed:
                existing.priority = max(existing.priority, priority)
                existing.repair_amount = max(existing.repair_amount, repair_amount)
                return existing

        request = MaintenanceRequest(
            building=building,
            priority=priority,
            repair_amount=repair_amount,
        )

        self.maintenance_queue.append(
            request,
        )

        return request

        # ========================================================

    # Assignment
    # ========================================================

    def assign_request(
        self,
        agent: Any,
        request: MaintenanceRequest,
    ) -> bool:

        if request.assigned_agent is not None:

            return False

        request.assigned_agent = agent

        return True

    def next_request(
        self,
    ) -> MaintenanceRequest | None:

        if not self.maintenance_queue:

            return None

        request = max(
            self.maintenance_queue,
            key=lambda r: r.priority,
        )

        self.maintenance_queue.remove(
            request,
        )

        return request

    # ========================================================
    # Completion
    # ========================================================

    def complete_request(
        self,
        request: MaintenanceRequest,
    ) -> None:

        request.completed = True

        request.building.repair(
            request.repair_amount,
        )

        self.completed_repairs += 1

    def fail_request(
        self,
        request: MaintenanceRequest,
    ) -> None:

        self.failed_repairs += 1

    # ========================================================
    # Inspection
    # ========================================================

    def inspect_buildings(
        self,
    ) -> None:

        self.inspections += 1

        for building in self.buildings.values():

            if building.needs_maintenance:

                self.request_maintenance(
                    building,
                    priority=2,
                )

    # ========================================================
    # Queries
    # ========================================================

    def pending_requests(
        self,
    ) -> list[MaintenanceRequest]:

        return [request for request in self.maintenance_queue if not request.completed]

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

        self.inspect_buildings()

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
                "pending_requests": len(
                    self.pending_requests(),
                ),
                "completed_repairs": self.completed_repairs,
                "failed_repairs": self.failed_repairs,
                "inspections": self.inspections,
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def clear_requests(
        self,
    ) -> None:

        self.maintenance_queue.clear()

    def clear(
        self,
    ) -> None:

        self.buildings.clear()

        self.maintenance_queue.clear()

        self.completed_repairs = 0

        self.failed_repairs = 0

        self.inspections = 0

    def __repr__(
        self,
    ) -> str:

        return (
            "MaintenanceManager("
            f"buildings={len(self.buildings)}, "
            f"requests={len(self.maintenance_queue)}, "
            f"completed={self.completed_repairs}"
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
                "completed_repairs": self.completed_repairs,
                "failed_repairs": self.failed_repairs,
                "inspections": self.inspections,
                "maintenance_queue": [
                    {
                        "building_id": request.building.building_id,
                        "priority": request.priority,
                        "repair_amount": request.repair_amount,
                        "completed": request.completed,
                    }
                    for request in self.maintenance_queue
                ],
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "MaintenanceManager":

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

        manager.completed_repairs = data.get(
            "completed_repairs",
            0,
        )

        manager.failed_repairs = data.get(
            "failed_repairs",
            0,
        )

        manager.inspections = data.get(
            "inspections",
            0,
        )

        # Building references are restored by ColonyModel
        # after all buildings have been deserialized.

        return manager


# ============================================================
# Canonical Alias
# ============================================================

Maintenance = MaintenanceManager
