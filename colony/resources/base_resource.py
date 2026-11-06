"""
base_resource.py

Canonical resource abstraction for Habryn.

Every colony resource inherits from BaseResource.

Responsibilities

- Storage
- Production
- Consumption
- Transfer
- Statistics
- Serialization
- Metadata
- Resource State
- Runtime
- Compatibility API

Hierarchy

BaseResource
├── Oxygen
├── Water
├── Food
├── Power
├── Heat
├── Fuel
├── Minerals
├── Waste
├── SciencePoints
├── Morale
└── Population
"""

from __future__ import annotations

from abc import ABC
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

# ============================================================
# Resource State
# ============================================================


class ResourceState(Enum):

    EMPTY = "Empty"

    LOW = "Low"

    NORMAL = "Normal"

    HIGH = "High"

    FULL = "Full"

    DISABLED = "Disabled"


# ============================================================
# Individual Storage Unit
# ============================================================


@dataclass(slots=True)
class ResourceStorage:

    name: str

    capacity: float

    amount: float = 0.0

    enabled: bool = True

    priority: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    # ========================================================
    # Properties
    # ========================================================

    @property
    def available_capacity(
        self,
    ) -> float:

        return max(
            0.0,
            self.capacity - self.amount,
        )

    @property
    def fill_percentage(
        self,
    ) -> float:

        if self.capacity <= 0:

            return 0.0

        return (self.amount / self.capacity) * 100.0

    @property
    def is_empty(
        self,
    ) -> bool:

        return self.amount <= 0.0

    @property
    def is_full(
        self,
    ) -> bool:

        return self.amount >= self.capacity

    def clamp(
        self,
    ) -> None:

        self.amount = max(
            0.0,
            min(
                self.capacity,
                self.amount,
            ),
        )


# ============================================================
# Base Resource
# ============================================================


@dataclass
class BaseResource(ABC):

    # ========================================================
    # Identity
    # ========================================================

    name: str = "Resource"

    unit: str = ""

    enabled: bool = True

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    # ========================================================
    # Storage
    # ========================================================

    storage: dict[str, ResourceStorage] = field(
        default_factory=dict,
    )

    # ========================================================
    # Runtime
    # ========================================================

    production_rate: float = 0.0

    consumption_rate: float = 0.0

    transfer_rate: float = 0.0

    loss_rate: float = 0.0

    # ========================================================
    # Statistics
    # ========================================================

    total_produced: float = 0.0

    total_consumed: float = 0.0

    total_transferred: float = 0.0

    total_lost: float = 0.0

    # ========================================================
    # State
    # ========================================================

    state: ResourceState = field(
        default=ResourceState.NORMAL,
        init=False,
    )

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        if not self.storage and self.storage_capacity > 0:

            self.add_storage(
                name="Primary",
                capacity=self.storage_capacity,
                amount=self.current_amount,
            )

        else:

            for storage in self.storage.values():

                storage.clamp()

            self._sync_fields()

        self._update_state()

    # ========================================================
    # Synchronization
    # ========================================================

    def _sync_fields(
        self,
    ) -> None:

        self.current_amount = sum(
            storage.amount for storage in self.storage.values() if storage.enabled
        )

        self.storage_capacity = sum(
            storage.capacity for storage in self.storage.values() if storage.enabled
        )

    # ========================================================
    # Compatibility Fields
    # ========================================================

    current_amount: float = 0.0

    storage_capacity: float = 0.0

    # ========================================================
    # Derived Properties
    # ========================================================

    @property
    def available_capacity(
        self,
    ) -> float:

        return max(
            0.0,
            self.storage_capacity - self.current_amount,
        )

    @property
    def fill_percentage(
        self,
    ) -> float:

        capacity = self.storage_capacity

        if capacity <= 0:

            return 0.0

        return (self.current_amount / capacity) * 100.0

    @property
    def storage_percentage(
        self,
    ) -> float:

        return self.fill_percentage

    @property
    def utilization(
        self,
    ) -> float:

        return self.fill_percentage

    @property
    def is_empty(
        self,
    ) -> bool:

        return self.current_amount <= 0.0

    @property
    def is_full(
        self,
    ) -> bool:

        return self.current_amount >= self.storage_capacity

    @property
    def storage_count(
        self,
    ) -> int:

        return len(
            self.storage,
        )

    @property
    def active_storage(
        self,
    ) -> list[ResourceStorage]:

        return [storage for storage in self.storage.values() if storage.enabled]

    # ========================================================
    # Storage Management
    # ========================================================

    def add_storage(
        self,
        name: str,
        capacity: float,
        amount: float = 0.0,
        priority: int = 0,
    ) -> None:

        self.storage[name] = ResourceStorage(
            name=name,
            capacity=max(
                0.0,
                capacity,
            ),
            amount=max(
                0.0,
                amount,
            ),
            priority=priority,
        )

        self.storage[name].clamp()

        self._sync_fields()

        self._update_state()

    def remove_storage(
        self,
        name: str,
    ) -> None:

        self.storage.pop(
            name,
            None,
        )

        self._update_state()

    def clear_storage(
        self,
    ) -> None:

        self.storage.clear()

        self._update_state()

    def get_storage(
        self,
        name: str,
    ) -> ResourceStorage | None:

        return self.storage.get(
            name,
        )

    def has_storage(
        self,
        name: str,
    ) -> bool:

        return name in self.storage

        # ========================================================

    # State Management
    # ========================================================

    def _update_state(
        self,
    ) -> None:

        if not self.enabled:

            self.state = ResourceState.DISABLED

            return

        fill = self.fill_percentage

        if fill <= 0.0:

            self.state = ResourceState.EMPTY

        elif fill <= 25.0:

            self.state = ResourceState.LOW

        elif fill >= 100.0:

            self.state = ResourceState.FULL

        elif fill >= 75.0:

            self.state = ResourceState.HIGH

        else:

            self.state = ResourceState.NORMAL

    # ========================================================
    # Resource Operations
    # ========================================================

    def add(
        self,
        amount: float,
    ) -> float:

        if not self.enabled or amount <= 0.0:

            return 0.0

        remaining = amount

        storages = sorted(
            self.active_storage,
            key=lambda s: s.priority,
        )

        for storage in storages:

            if remaining <= 0.0:

                break

            accepted = min(
                remaining,
                storage.available_capacity,
            )

            storage.amount += accepted

            remaining -= accepted

        produced = amount - remaining

        self.total_produced += produced

        self._sync_fields()

        self._update_state()

        return produced

    def produce(
        self,
        amount: float,
    ) -> float:

        return self.add(
            amount,
        )

    def generate(
        self,
        amount: float,
    ) -> float:

        return self.produce(
            amount,
        )

    def consume(
        self,
        amount: float,
    ) -> float:

        if not self.enabled or amount <= 0.0:

            return 0.0

        remaining = amount

        storages = sorted(
            self.active_storage,
            key=lambda s: s.priority,
            reverse=True,
        )

        for storage in storages:

            if remaining <= 0.0:

                break

            removed = min(
                storage.amount,
                remaining,
            )

            storage.amount -= removed

            remaining -= removed

        consumed = amount - remaining

        self.total_consumed += consumed

        self._sync_fields()

        self._update_state()

        return consumed

    def remove(
        self,
        amount: float,
    ) -> float:

        return self.consume(
            amount,
        )

    def lose(
        self,
        amount: float,
    ) -> float:

        lost = self.consume(
            amount,
        )

        self.total_lost += lost

        return lost

        # ========================================================

    # Transfer
    # ========================================================

    def transfer(
        self,
        target: "BaseResource",
        amount: float,
    ) -> float:

        if target is self or amount <= 0.0:

            return 0.0

        removed = self.consume(
            amount,
        )

        if removed <= 0.0:

            return 0.0

        accepted = target.add(
            removed,
        )

        if accepted < removed:

            self.add(
                removed - accepted,
            )

        self.total_transferred += accepted

        return accepted

    def transfer_to(
        self,
        target: "BaseResource",
        amount: float,
    ) -> float:

        return self.transfer(
            target,
            amount,
        )

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        if not self.enabled:

            return

        if self.production_rate > 0.0:

            self.add(
                self.production_rate,
            )

        if self.consumption_rate > 0.0:

            self.consume(
                self.consumption_rate,
            )

        if self.loss_rate > 0.0:

            self.lose(
                self.loss_rate,
            )

        self._update_state()

    def hourly_update(
        self,
    ) -> None:

        self.step()

    def daily_update(
        self,
    ) -> None:

        self._update_state()

    # ========================================================
    # Reset / Utility
    # ========================================================

    def refill(
        self,
    ) -> None:

        for storage in self.active_storage:

            storage.amount = storage.capacity

        self._update_state()

    def empty(
        self,
    ) -> None:

        for storage in self.active_storage:

            storage.amount = 0.0

        self._update_state()

    def reset_statistics(
        self,
    ) -> None:

        self.total_produced = 0.0

        self.total_consumed = 0.0

        self.total_transferred = 0.0

        self.total_lost = 0.0

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict[str, Any]:

        data = {
            "name": self.name,
            "unit": self.unit,
            "enabled": self.enabled,
            "production_rate": self.production_rate,
            "consumption_rate": self.consumption_rate,
            "transfer_rate": self.transfer_rate,
            "loss_rate": self.loss_rate,
            "total_produced": self.total_produced,
            "total_consumed": self.total_consumed,
            "total_transferred": self.total_transferred,
            "total_lost": self.total_lost,
            "metadata": dict(self.metadata),
            "storage": {
                name: asdict(storage) for name, storage in self.storage.items()
            },
        }

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
    ) -> "BaseResource":

        storages: dict[
            str,
            ResourceStorage,
        ] = {}

        for name, values in data.get(
            "storage",
            {},
        ).items():

            storages[name] = ResourceStorage(
                **values,
            )

        resource = cls(
            name=data.get(
                "name",
                "Resource",
            ),
            unit=data.get(
                "unit",
                "",
            ),
            enabled=data.get(
                "enabled",
                True,
            ),
            metadata=dict(
                data.get(
                    "metadata",
                    {},
                )
            ),
            storage=storages,
            production_rate=data.get(
                "production_rate",
                0.0,
            ),
            consumption_rate=data.get(
                "consumption_rate",
                0.0,
            ),
            transfer_rate=data.get(
                "transfer_rate",
                0.0,
            ),
            loss_rate=data.get(
                "loss_rate",
                0.0,
            ),
        )

        resource.total_produced = data.get(
            "total_produced",
            0.0,
        )

        resource.total_consumed = data.get(
            "total_consumed",
            0.0,
        )

        resource.total_transferred = data.get(
            "total_transferred",
            0.0,
        )

        resource.total_lost = data.get(
            "total_lost",
            0.0,
        )

        resource._update_state()

        return resource

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict[str, Any]:

        return {
            "name": self.name,
            "unit": self.unit,
            "enabled": self.enabled,
            "state": self.state.value,
            "storage_count": self.storage_count,
            "current_amount": round(
                self.current_amount,
                2,
            ),
            "storage_capacity": round(
                self.storage_capacity,
                2,
            ),
            "available_capacity": round(
                self.available_capacity,
                2,
            ),
            "fill_percentage": round(
                self.fill_percentage,
                2,
            ),
            "production_rate": round(
                self.production_rate,
                2,
            ),
            "consumption_rate": round(
                self.consumption_rate,
                2,
            ),
            "transfer_rate": round(
                self.transfer_rate,
                2,
            ),
            "loss_rate": round(
                self.loss_rate,
                2,
            ),
            "total_produced": round(
                self.total_produced,
                2,
            ),
            "total_consumed": round(
                self.total_consumed,
                2,
            ),
            "total_transferred": round(
                self.total_transferred,
                2,
            ),
            "total_lost": round(
                self.total_lost,
                2,
            ),
            "storages": {
                name: {
                    "amount": round(
                        storage.amount,
                        2,
                    ),
                    "capacity": round(
                        storage.capacity,
                        2,
                    ),
                    "fill_percentage": round(
                        storage.fill_percentage,
                        2,
                    ),
                    "enabled": storage.enabled,
                    "priority": storage.priority,
                }
                for name, storage in self.storage.items()
            },
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

    def remove_metadata(
        self,
        key: str,
    ) -> None:

        self.metadata.pop(
            key,
            None,
        )

    def clear_metadata(
        self,
    ) -> None:

        self.metadata.clear()  # ========================================================

    # Configuration
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

    def set_production_rate(
        self,
        rate: float,
    ) -> None:

        self.production_rate = max(
            0.0,
            rate,
        )

    def set_consumption_rate(
        self,
        rate: float,
    ) -> None:

        self.consumption_rate = max(
            0.0,
            rate,
        )

    def set_transfer_rate(
        self,
        rate: float,
    ) -> None:

        self.transfer_rate = max(
            0.0,
            rate,
        )

    def set_loss_rate(
        self,
        rate: float,
    ) -> None:

        self.loss_rate = max(
            0.0,
            rate,
        )

    # ========================================================
    # Internal Helpers
    # ========================================================

    def _production_order(
        self,
    ) -> list[ResourceStorage]:

        return sorted(
            self.active_storage,
            key=lambda storage: (
                storage.priority,
                storage.name,
            ),
        )

    def _consumption_order(
        self,
    ) -> list[ResourceStorage]:

        return sorted(
            self.active_storage,
            key=lambda storage: (
                storage.priority,
                storage.name,
            ),
            reverse=True,
        )

    def __len__(
        self,
    ) -> int:

        return self.storage_count

    def __bool__(
        self,
    ) -> bool:

        return self.enabled and not self.is_empty

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "BaseResource("
            f"name='{self.name}', "
            f"amount={self.current_amount:.2f}{self.unit}, "
            f"capacity={self.storage_capacity:.2f}{self.unit}, "
            f"fill={self.fill_percentage:.1f}%, "
            f"storages={self.storage_count}, "
            f"state='{self.state.value}'"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Resource = BaseResource
