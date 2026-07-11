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

from colony.resources.base_resource import BaseResource
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

        self.resources[

            resource.name

        ] = resource

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

        return (

            name

            in self.resources

        )
    
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

        resource.generate(

            amount,

        )

        self.production_history[

            resource_name

        ] = (

            self.production_history.get(

                resource_name,

                0.0,

            )

            + amount

        )

        self.shortages.discard(

            resource_name,

        )

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

            return False

        success = resource.consume(

            amount,

        )

        if not success:

            self.shortages.add(

                resource_name,

            )

            return False

        self.consumption_history[

            resource_name

        ] = (

            self.consumption_history.get(

                resource_name,

                0.0,

            )

            + amount

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

        self.transfer_history[

            resource_name

        ] = (

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

        self.shortages.clear()

        self.surpluses.clear()

        for name, resource in self.resources.items():

            percentage = (

                resource.storage_percentage

            )

            if percentage <= 10.0:

                self.shortages.add(

                    name,

                )

            elif percentage >= 90.0:

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

                "resource_count":
                self.resource_count,

                "healthy_colony":
                self.healthy_colony,

                "registered_resources":
                sorted(

                    self.resources.keys(),

                ),

                "shortages":
                sorted(

                    self.shortages,

                ),

                "surpluses":
                sorted(

                    self.surpluses,

                ),

                "total_produced":
                round(

                    self.total_produced(),

                    2,

                ),

                "total_consumed":
                round(

                    self.total_consumed(),

                    2,

                ),

                "total_transferred":
                round(

                    self.total_transferred(),

                    2,

                ),

                "production_history":
                dict(

                    self.production_history,

                ),

                "consumption_history":
                dict(

                    self.consumption_history,

                ),

                "transfer_history":
                dict(

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

            name: resource.current_amount

            for name, resource in self.resources.items()

        }
    
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

ColonyResources = ResourceManager