"""
resource_manager.py

Canonical colony-wide resource manager.

Tracks production, consumption,
storage and transfers for every
resource in Habryn.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import importlib

from colony.resources.base_resource import BaseResource, ResourceStorage
from colony.systems.base_manager import BaseManager

# ============================================================
# Resource Manager
# ============================================================


@dataclass
class ResourceManager(BaseManager):

    name: str = "Resource Manager"

    resources: dict[
        str,
        BaseResource,
    ] = field(
        default_factory=dict,
    )

    production_history: dict[
        str,
        float,
    ] = field(
        default_factory=dict,
    )

    consumption_history: dict[
        str,
        float,
    ] = field(
        default_factory=dict,
    )

    transfer_history: dict[
        str,
        float,
    ] = field(
        default_factory=dict,
    )

    shortages: set[str] = field(
        default_factory=set,
    )

    failed_shortages: set[str] = field(default_factory=set)

    surpluses: set[str] = field(
        default_factory=set,
    )

    # ========================================================
    # Registration
    # ========================================================

    def register_resource(
        self,
        resource: BaseResource,
    ) -> None:

        self.resources[resource.name] = resource

    def unregister_resource(
        self,
        name: str,
    ) -> None:

        self.resources.pop(
            name,
            None,
        )

    def resource(
        self,
        name: str,
    ) -> BaseResource | None:

        return self.resources.get(
            name,
        )

    def has_resource(
        self,
        name: str,
    ) -> bool:

        return name in self.resources

    # ========================================================
    # Production
    # ========================================================

    def produce(
        self,
        resource_name: str,
        amount: float,
    ) -> bool:

        resource = self.resource(
            resource_name,
        )

        if resource is None:

            return False

        if amount <= 0.0:
            return False

        accepted = resource.generate(amount)
        if accepted <= 0.0:
            return False

        self.production_history[resource_name] = (
            self.production_history.get(
                resource_name,
                0.0,
            )
            + accepted
        )

        if resource.storage_percentage > 10.0:
            self.shortages.discard(resource_name)

        return True

    # ========================================================
    # Consumption
    # ========================================================

    def consume(
        self,
        resource_name: str,
        amount: float,
    ) -> bool:

        resource = self.resource(
            resource_name,
        )

        if resource is None:

            self.shortages.add(resource_name)
            self.failed_shortages.add(resource_name)
            return False

        if amount <= 0.0:
            return False

        if resource.current_amount < amount:

            self.shortages.add(
                resource_name,
            )
            self.failed_shortages.add(resource_name)

            return False

        consumed = resource.consume(amount)
        if consumed < amount:
            self.shortages.add(resource_name)
            self.failed_shortages.add(resource_name)
            return False

        self.failed_shortages.discard(resource_name)
        if resource.storage_percentage > 10.0:
            self.shortages.discard(resource_name)

        self.consumption_history[resource_name] = (
            self.consumption_history.get(
                resource_name,
                0.0,
            )
            + consumed
        )

        return True

    # ========================================================
    # Transfers
    # ========================================================

    def transfer(
        self,
        resource_name: str,
        amount: float,
    ) -> bool:

        resource = self.resource(
            resource_name,
        )

        if resource is None:

            return False

        self.transfer_history[resource_name] = (
            self.transfer_history.get(
                resource_name,
                0.0,
            )
            + amount
        )

        return True

    # ========================================================
    # Queries
    # ========================================================

    def amount(
        self,
        resource_name: str,
    ) -> float:

        resource = self.resource(
            resource_name,
        )

        if resource is None:

            return 0.0

        return resource.current_amount

    def capacity(
        self,
        resource_name: str,
    ) -> float:

        resource = self.resource(
            resource_name,
        )

        if resource is None:

            return 0.0

        return resource.storage_capacity

    # ========================================================
    # Resource Analysis
    # ========================================================

    def available_resources(
        self,
    ) -> list[str]:

        return [
            name
            for name, resource in self.resources.items()
            if resource.current_amount > 0
        ]

    def empty_resources(
        self,
    ) -> list[str]:

        return [
            name
            for name, resource in self.resources.items()
            if resource.current_amount <= 0
        ]

    def storage_percentage(
        self,
        resource_name: str,
    ) -> float:

        resource = self.resource(
            resource_name,
        )

        if resource is None:

            return 0.0

        return resource.storage_percentage

    def total_resources(
        self,
    ) -> int:

        return len(
            self.resources,
        )

    # ========================================================
    # Colony Status
    # ========================================================

    def update_status(
        self,
    ) -> None:

        self.surpluses.clear()

        for name, resource in self.resources.items():

            if name in {"Population", "Morale", "Science Points"}:
                continue

            percentage = resource.storage_percentage

            if percentage <= 10.0 or name in self.failed_shortages:
                self.shortages.add(name)
            else:
                self.shortages.discard(name)

            if percentage >= 90.0:

                self.surpluses.add(
                    name,
                )

    @property
    def healthy_colony(
        self,
    ) -> bool:

        return (
            len(
                self.shortages,
            )
            == 0
        )

    @property
    def resource_count(
        self,
    ) -> int:

        return len(
            self.resources,
        )

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.enabled:

            return

        self.update_status()

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

        self.update_status()

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

        self.update_status()

    # ========================================================
    # History
    # ========================================================

    def total_produced(
        self,
    ) -> float:

        return sum(
            self.production_history.values(),
        )

    def total_consumed(
        self,
    ) -> float:

        return sum(
            self.consumption_history.values(),
        )

    def total_transferred(
        self,
    ) -> float:

        return sum(
            self.transfer_history.values(),
        )

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "resource_count": self.resource_count,
                "healthy_colony": self.healthy_colony,
                "registered_resources": sorted(
                    self.resources.keys(),
                ),
                "shortages": sorted(
                    self.shortages,
                ),
                "surpluses": sorted(
                    self.surpluses,
                ),
                "total_produced": round(
                    self.total_produced(),
                    2,
                ),
                "total_consumed": round(
                    self.total_consumed(),
                    2,
                ),
                "total_transferred": round(
                    self.total_transferred(),
                    2,
                ),
                "production_history": dict(
                    self.production_history,
                ),
                "consumption_history": dict(
                    self.consumption_history,
                ),
                "transfer_history": dict(
                    self.transfer_history,
                ),
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def reset_statistics(
        self,
    ) -> None:

        self.production_history.clear()

        self.consumption_history.clear()

        self.transfer_history.clear()

        self.shortages.clear()

        self.surpluses.clear()

    def clear_resources(
        self,
    ) -> None:

        self.resources.clear()

        self.reset_statistics()

    def resource_names(
        self,
    ) -> list[str]:

        return sorted(
            self.resources.keys(),
        )

    def resource_summary(
        self,
    ) -> dict[str, float]:

        return {
            name: resource.current_amount for name, resource in self.resources.items()
        }

    def serialize(self) -> dict:
        """Persist every registered resource and manager ledger."""
        data = super().serialize()
        data.update({
            "resources": {
                name: {"class": f"{type(resource).__module__}.{type(resource).__name__}",
                       "data": resource.serialize()}
                for name, resource in self.resources.items()
            },
            "production_history": dict(self.production_history),
            "consumption_history": dict(self.consumption_history),
            "transfer_history": dict(self.transfer_history),
            "shortages": sorted(self.shortages),
            "failed_shortages": sorted(self.failed_shortages),
            "surpluses": sorted(self.surpluses),
        })
        return data

    @classmethod
    def deserialize(cls, data: dict) -> "ResourceManager":
        manager = cls()
        _restore_manager_counters(manager, data)
        for name, saved in data.get("resources", {}).items():
            module_name, class_name = saved["class"].rsplit(".", 1)
            if not module_name.startswith("colony.resources."):
                raise ValueError(f"Unsupported saved resource class: {saved['class']}")
            resource_class = getattr(importlib.import_module(module_name), class_name)
            resource = resource_class.deserialize(saved["data"])
            resource_data = saved["data"]
            resource.storage = {
                storage_name: ResourceStorage(**storage_data)
                for storage_name, storage_data in resource_data.get("storage", {}).items()
            }
            resource.enabled = resource_data.get("enabled", True)
            resource.metadata = dict(resource_data.get("metadata", {}))
            resource.production_rate = resource_data.get("production_rate", 0.0)
            resource.consumption_rate = resource_data.get("consumption_rate", 0.0)
            resource.transfer_rate = resource_data.get("transfer_rate", 0.0)
            resource.loss_rate = resource_data.get("loss_rate", 0.0)
            resource.total_produced = resource_data.get("total_produced", 0.0)
            resource.total_consumed = resource_data.get("total_consumed", 0.0)
            resource.total_transferred = resource_data.get("total_transferred", 0.0)
            resource.total_lost = resource_data.get("total_lost", 0.0)
            resource._sync_fields()
            resource._update_state()
            manager.register_resource(resource)
        manager.production_history = dict(data.get("production_history", {}))
        manager.consumption_history = dict(data.get("consumption_history", {}))
        manager.transfer_history = dict(data.get("transfer_history", {}))
        manager.shortages = set(data.get("shortages", ()))
        manager.failed_shortages = set(data.get("failed_shortages", ()))
        manager.surpluses = set(data.get("surpluses", ()))
        return manager


    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "ResourceManager("
            f"resources={self.resource_count}, "
            f"healthy={self.healthy_colony}, "
            f"shortages={len(self.shortages)}, "
            f"surpluses={len(self.surpluses)}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================


def _restore_manager_counters(manager, data: dict) -> None:
    for key in ("enabled", "initialized", "tick_count", "hour_count", "day_count",
                "update_count", "error_count"):
        if key in data:
            setattr(manager, key, data[key])

ColonyResources = ResourceManager
