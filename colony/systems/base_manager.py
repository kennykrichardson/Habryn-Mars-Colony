"""
base_manager.py

Part 1/3

Canonical base class for every manager in Habryn.

Inheritance

BaseManager
├── AIManager
├── TaskManager
├── EconomyManager
├── EmergencyManager
├── MaintenanceManager
├── LogisticsManager
├── ResearchManager
└── ConstructionManager

Managers coordinate systems.

They do not own simulation entities.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

# ============================================================
# Manager State
# ============================================================


class ManagerState(Enum):

    STOPPED = "Stopped"

    INITIALIZING = "Initializing"

    RUNNING = "Running"

    PAUSED = "Paused"

    DISABLED = "Disabled"

    ERROR = "Error"


# ============================================================
# Base Manager
# ============================================================


@dataclass
class BaseManager:

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    name: str

    enabled: bool = True

    initialized: bool = False

    state: ManagerState = ManagerState.STOPPED

    # --------------------------------------------------------
    # Runtime
    # --------------------------------------------------------

    tick_count: int = 0

    hour_count: int = 0

    day_count: int = 0

    update_count: int = 0

    error_count: int = 0

    # --------------------------------------------------------
    # Registry
    # --------------------------------------------------------

    registry: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)

    # ========================================================
    # Lifecycle
    # ========================================================

    def initialize(
        self,
    ) -> None:

        if self.initialized:

            return

        self.state = ManagerState.INITIALIZING

        self.initialized = True

        self.state = ManagerState.RUNNING

    def shutdown(
        self,
    ) -> None:

        self.initialized = False

        self.state = ManagerState.STOPPED

    def enable(
        self,
    ) -> None:

        self.enabled = True

        self.state = ManagerState.RUNNING

    def disable(
        self,
    ) -> None:

        self.enabled = False

        self.state = ManagerState.DISABLED

    def pause(
        self,
    ) -> None:

        if self.state == ManagerState.RUNNING:

            self.state = ManagerState.PAUSED

    def resume(
        self,
    ) -> None:

        if self.enabled:

            self.state = ManagerState.RUNNING

    # ========================================================
    # Registration
    # ========================================================

    def register(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.registry[key] = value

    def unregister(
        self,
        key: str,
    ) -> None:

        self.registry.pop(
            key,
            None,
        )

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.registry.get(
            key,
            default,
        )

    def clear_registry(
        self,
    ) -> None:

        self.registry.clear()

        # ========================================================

    # Update Loop
    # ========================================================

    def step(
        self,
    ) -> None:

        if not self.enabled or not self.initialized:
            return

        self.tick_count += 1

        self.update_count += 1

    def hourly_update(
        self,
    ) -> None:

        if not self.enabled or not self.initialized:
            return

        self.hour_count += 1

    def daily_update(
        self,
    ) -> None:

        if not self.enabled or not self.initialized:
            return

        self.day_count += 1

    # ========================================================
    # Error Handling
    # ========================================================

    def report_error(
        self,
        error: Exception | str,
    ) -> None:

        self.error_count += 1

        self.state = ManagerState.ERROR

        self.metadata["last_error"] = str(
            error,
        )

    def clear_error(
        self,
    ) -> None:

        self.metadata.pop(
            "last_error",
            None,
        )

        if self.enabled:

            self.state = ManagerState.RUNNING

    # ========================================================
    # Reset
    # ========================================================

    def reset(
        self,
    ) -> None:

        self.tick_count = 0

        self.hour_count = 0

        self.day_count = 0

        self.update_count = 0

        self.error_count = 0

        self.registry.clear()

        self.metadata.clear()

        self.state = ManagerState.STOPPED

        self.initialized = False

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

    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict[str, Any]:

        data = asdict(self)

        data["state"] = self.state.value

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
    ) -> "BaseManager":

        state = ManagerState(
            data.pop(
                "state",
            ),
        )

        manager = cls(
            **data,
        )

        manager.state = state

        return manager

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict[str, Any]:
        """
        Public telemetry exposed to Mission Control.

        Override in subclasses to expose
        colony-facing information.
        """

        return {

            "name": self.name,

            "enabled": self.enabled,

            "initialized": self.initialized,

            "state": self.state.value,

        }


    def debug_statistics(
        self,
    ) -> dict[str, Any]:
        """
        Internal diagnostics for developers.
        """

        stats = self.statistics()

        stats.update({

            "tick_count": self.tick_count,

            "hour_count": self.hour_count,

            "day_count": self.day_count,

            "update_count": self.update_count,

            "error_count": self.error_count,

            "registered_objects": len(

                self.registry,

            ),

        })

        if self.metadata:

            stats["metadata"] = self.metadata.copy()

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def __len__(
        self,
    ) -> int:

        return len(
            self.registry,
        )

    def __contains__(
        self,
        key: str,
    ) -> bool:

        return key in self.registry

    def __repr__(
        self,
    ) -> str:

        return (
            "BaseManager("
            f"name='{self.name}', "
            f"state='{self.state.value}', "
            f"enabled={self.enabled}, "
            f"registered={len(self.registry)}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Manager = BaseManager
