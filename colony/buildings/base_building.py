"""
base_building.py

Part 1/4

Canonical building abstraction for Habryn.

Inheritance

BaseBuilding
├── Habitat
├── Greenhouse
├── Laboratory
├── SolarArray
├── Battery
├── Reactor
├── WaterPlant
├── OxygenGenerator
├── Mine
├── Workshop
├── Storage
└── Hospital

Every constructible structure inherits from BaseBuilding.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

# ============================================================
# Building State
# ============================================================


class BuildingState(Enum):

    CONSTRUCTION = "Construction"

    ACTIVE = "Active"

    IDLE = "Idle"

    DISABLED = "Disabled"

    DAMAGED = "Damaged"

    DESTROYED = "Destroyed"


# ============================================================
# Base Building
# ============================================================


@dataclass
class BaseBuilding:

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    building_id: int

    name: str

    position: tuple[int, int]

    # --------------------------------------------------------
    # Runtime
    # --------------------------------------------------------

    enabled: bool = True

    powered: bool = True

    constructed: bool = True

    state: BuildingState = BuildingState.ACTIVE

    # ========================================================
    # Power Management
    # ========================================================

    # Determines the order in which the PowerGrid supplies
    # electricity during shortages.
    #
    # Lower value = higher priority.
    #
    # Example:
    # 10  -> Oxygen Generator
    # 20  -> Water Plant
    # 70  -> Workshop
    # 100 -> Launch Pad

    power_priority: int = 100

    # Minimum amount of power required before this building
    # can remain operational.
    minimum_power: float = 0.0

    # Updated automatically by the PowerGrid.
    is_powered: bool = True

    # Whether this building participates in the electrical grid.
    receives_power: bool = True

    # Used during disasters or manual shutdowns.
    emergency_shutdown: bool = False

    # --------------------------------------------------------
    # Integrity
    # --------------------------------------------------------

    integrity: float = 100.0

    max_integrity: float = 100.0

    maintenance: float = 100.0

    efficiency: float = 1.0

    # --------------------------------------------------------
    # Power
    # --------------------------------------------------------

    power_required: float = 0.0

    power_consumption: float = 0.0

    power_production: float = 0.0

    # --------------------------------------------------------
    # Resources
    # --------------------------------------------------------

    resource_input: dict[str, float] = field(default_factory=dict)

    resource_output: dict[str, float] = field(default_factory=dict)

    storage: dict[str, float] = field(default_factory=dict)

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    hours_operated: int = 0

    repairs_received: int = 0

    upgrades_received: int = 0

    total_production: float = 0.0

    total_consumption: float = 0.0

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata: dict[str, Any] = field(default_factory=dict)

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        self.integrity = max(
            0.0,
            min(
                self.integrity,
                self.max_integrity,
            ),
        )

        self.maintenance = max(
            0.0,
            min(
                100.0,
                self.maintenance,
            ),
        )

        self._update_state()

    # ========================================================
    # Properties
    # ========================================================

    @property
    def operational(
        self,
    ) -> bool:

        return self.constructed and self.enabled and self.powered and self.integrity > 0

    @property
    def damaged(
        self,
    ) -> bool:

        return self.integrity < self.max_integrity

    @property
    def destroyed(
        self,
    ) -> bool:

        return self.integrity <= 0

    @property
    def needs_maintenance(
        self,
    ) -> bool:

        return self.maintenance < 40

    @property
    def health_percentage(
        self,
    ) -> float:

        if self.max_integrity <= 0:

            return 0.0

        return (self.integrity / self.max_integrity) * 100.0

        # ========================================================

    # State
    # ========================================================

    def _update_state(
        self,
    ) -> None:

        if not self.constructed:

            self.state = BuildingState.CONSTRUCTION

            return

        if self.integrity <= 0:

            self.state = BuildingState.DESTROYED

            return

        if self.integrity < (self.max_integrity * 0.35):

            self.state = BuildingState.DAMAGED

            return

        if not self.enabled:

            self.state = BuildingState.DISABLED

            return

        if not self.powered:

            self.state = BuildingState.IDLE

            return

        self.state = BuildingState.ACTIVE

    # ========================================================
    # Power
    # ========================================================

    def set_power(
        self,
        powered: bool,
    ) -> None:

        self.powered = powered

        self.is_powered = powered

        self._update_state()

    # ========================================================
    # Enable / Disable
    # ========================================================

    def enable(
        self,
    ) -> None:

        self.enabled = True

        self._update_state()

    def disable(
        self,
    ) -> None:

        self.enabled = False

        self._update_state()

    # ========================================================
    # Damage / Repair
    # ========================================================

    def damage(
        self,
        amount: float,
    ) -> None:

        self.integrity = max(
            0.0,
            self.integrity - amount,
        )

        self._update_state()

    def repair(
        self,
        amount: float,
    ) -> None:

        self.integrity = min(
            self.max_integrity,
            self.integrity + amount,
        )

        self.repairs_received += 1

        self._update_state()

    def upgrade(
        self,
        efficiency_bonus: float = 0.05,
    ) -> None:

        self.efficiency += efficiency_bonus

        self.upgrades_received += 1

    def maintain(
        self,
        amount: float = 5.0,
    ) -> None:

        self.maintenance = min(
            100.0,
            self.maintenance + amount,
        )

        # ========================================================

    # Resources
    # ========================================================

    def add_resource_input(
        self,
        resource: str,
        amount: float,
    ) -> None:

        self.resource_input[resource] = amount

    def add_resource_output(
        self,
        resource: str,
        amount: float,
    ) -> None:

        self.resource_output[resource] = amount

    def add_storage(
        self,
        resource: str,
        amount: float = 0.0,
    ) -> None:

        self.storage[resource] = amount

    def set_storage(
        self,
        resource: str,
        amount: float,
    ) -> None:

        self.storage[resource] = max(
            0.0,
            amount,
        )

    def get_storage(
        self,
        resource: str,
    ) -> float:

        return self.storage.get(
            resource,
            0.0,
        )

    def consume_resource(
        self,
        resource: str,
        amount: float,
    ) -> bool:

        available = self.storage.get(
            resource,
            0.0,
        )

        if available < amount:

            return False

        self.storage[resource] -= amount

        self.total_consumption += amount

        return True

    def produce_resource(
        self,
        resource: str,
        amount: float,
    ) -> None:

        self.storage[resource] = (
            self.storage.get(
                resource,
                0.0,
            )
            + amount
        )

        self.total_production += amount

    # ========================================================
    # Update Loop
    # ========================================================

    def step(
        self,
    ) -> None:

        if not self.operational:

            return

        if self.receives_power and not self.is_powered:

            return

        if self.emergency_shutdown:

            return

        self.hours_operated += 1

        self._update_state()

    def hourly_update(
        self,
    ) -> None:

        self.step()

        self.maintenance = max(
            0.0,
            self.maintenance - 0.02,
        )

        if self.maintenance < 40:

            self.damage(
                0.02,
            )

    def daily_update(
        self,
    ) -> None:

        self._update_state()

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
    ) -> "BaseBuilding":

        state = BuildingState(
            data.pop(
                "state",
            ),
        )

        building = cls(
            **data,
        )

        building.state = state

        return building

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict[str, Any]:

        return {
            "id": self.building_id,
            "name": self.name,
            "state": self.state.value,
            "position": self.position,
            "enabled": self.enabled,
            "powered": self.powered,
            "constructed": self.constructed,
            "integrity": round(
                self.integrity,
                2,
            ),
            "max_integrity": round(
                self.max_integrity,
                2,
            ),
            "health_percentage": round(
                self.health_percentage,
                2,
            ),
            "maintenance": round(
                self.maintenance,
                2,
            ),
            "efficiency": round(
                self.efficiency,
                2,
            ),
            "power_required": round(
                self.power_required,
                2,
            ),
            "power_consumption": round(
                self.power_consumption,
                2,
            ),
            "power_production": round(
                self.power_production,
                2,
            ),
            "resource_input": dict(
                self.resource_input,
            ),
            "resource_output": dict(
                self.resource_output,
            ),
            "storage": dict(
                self.storage,
            ),
            "hours_operated": self.hours_operated,
            "repairs_received": self.repairs_received,
            "upgrades_received": self.upgrades_received,
            "total_production": round(
                self.total_production,
                2,
            ),
            "total_consumption": round(
                self.total_consumption,
                2,
            ),
        }

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
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "BaseBuilding("
            f"id={self.building_id}, "
            f"name='{self.name}', "
            f"state='{self.state.value}', "
            f"health={self.health_percentage:.1f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Building = BaseBuilding
