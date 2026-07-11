"""
emergency_manager.py

Part 1/4

Canonical Emergency Manager.

Responsible for colony emergencies.

Owns

- emergency queue
- active emergencies
- alert escalation
- emergency responders

Does NOT resolve emergencies.

Agents and robots resolve them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from enum import Enum
from typing import Any

from colony.systems.base_manager import BaseManager

# ============================================================
# Emergency Severity
# ============================================================


class EmergencySeverity(Enum):

    LOW = 1

    MEDIUM = 2

    HIGH = 3

    CRITICAL = 4


# ============================================================
# Emergency
# ============================================================


@dataclass(slots=True)
class Emergency:

    title: str

    description: str

    severity: EmergencySeverity

    source: Any | None = None

    target: Any | None = None

    location: tuple[int, int] | None = None

    assigned_agent: Any | None = None

    resolved: bool = False


# ============================================================
# Emergency Manager
# ============================================================


@dataclass
class EmergencyManager(BaseManager):

    name: str = "Emergency Manager"

    emergency_queue: deque[Emergency] = field(default_factory=deque)

    active_emergencies: list[Emergency] = field(default_factory=list)

    resolved_emergencies: int = 0

    failed_emergencies: int = 0

    # ========================================================
    # Registration
    # ========================================================

    def report_emergency(
        self,
        title: str,
        description: str,
        severity: EmergencySeverity,
        source: Any | None = None,
        target: Any | None = None,
        location: tuple[int, int] | None = None,
    ) -> Emergency:

        emergency = Emergency(
            title=title,
            description=description,
            severity=severity,
            source=source,
            target=target,
            location=location,
        )

        self.emergency_queue.append(
            emergency,
        )

        return emergency

    # ========================================================
    # Assignment
    # ========================================================

    def assign_emergency(
        self,
        agent: Any,
        emergency: Emergency,
    ) -> bool:

        if emergency.assigned_agent is not None:

            return False

        emergency.assigned_agent = agent

        self.active_emergencies.append(
            emergency,
        )

        if emergency in self.emergency_queue:

            self.emergency_queue.remove(
                emergency,
            )

        return True

    # ========================================================
    # Resolution
    # ========================================================

    def resolve_emergency(
        self,
        emergency: Emergency,
    ) -> None:

        emergency.resolved = True

        if emergency in self.active_emergencies:

            self.active_emergencies.remove(
                emergency,
            )

        self.resolved_emergencies += 1

    def fail_emergency(
        self,
        emergency: Emergency,
    ) -> None:

        if emergency in self.active_emergencies:

            self.active_emergencies.remove(
                emergency,
            )

        self.failed_emergencies += 1

    # ========================================================
    # Queries
    # ========================================================

    def next_emergency(
        self,
    ) -> Emergency | None:

        if not self.emergency_queue:

            return None

        emergency = max(
            self.emergency_queue,
            key=lambda e: e.severity.value,
        )

        self.emergency_queue.remove(
            emergency,
        )

        self.active_emergencies.append(
            emergency,
        )

        return emergency

    def pending_emergencies(
        self,
    ) -> list[Emergency]:

        return list(
            self.emergency_queue,
        )

    def critical_emergencies(
        self,
    ) -> list[Emergency]:

        return [
            emergency
            for emergency in self.active_emergencies
            if emergency.severity == EmergencySeverity.CRITICAL
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
                "pending_emergencies": len(
                    self.emergency_queue,
                ),
                "active_emergencies": len(
                    self.active_emergencies,
                ),
                "resolved_emergencies": self.resolved_emergencies,
                "failed_emergencies": self.failed_emergencies,
                "critical_emergencies": len(
                    self.critical_emergencies(),
                ),
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def clear(
        self,
    ) -> None:

        self.emergency_queue.clear()

        self.active_emergencies.clear()

        self.resolved_emergencies = 0

        self.failed_emergencies = 0

    def __repr__(
        self,
    ) -> str:

        return (
            "EmergencyManager("
            f"pending={len(self.emergency_queue)}, "
            f"active={len(self.active_emergencies)}, "
            f"resolved={self.resolved_emergencies}"
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
                "resolved_emergencies": self.resolved_emergencies,
                "failed_emergencies": self.failed_emergencies,
                "active_emergencies": [
                    {
                        "title": emergency.title,
                        "description": emergency.description,
                        "severity": emergency.severity.value,
                        "location": emergency.location,
                        "resolved": emergency.resolved,
                    }
                    for emergency in self.active_emergencies
                ],
                "pending_emergencies": [
                    {
                        "title": emergency.title,
                        "description": emergency.description,
                        "severity": emergency.severity.value,
                        "location": emergency.location,
                        "resolved": emergency.resolved,
                    }
                    for emergency in self.emergency_queue
                ],
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "EmergencyManager":

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

        manager.resolved_emergencies = data.get(
            "resolved_emergencies",
            0,
        )

        manager.failed_emergencies = data.get(
            "failed_emergencies",
            0,
        )

        return manager


# ============================================================
# Canonical Alias
# ============================================================

EmergencySystem = EmergencyManager
