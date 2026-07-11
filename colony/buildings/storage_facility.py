"""
storage_facility.py

Part 1/6

Canonical Storage Facility.

Stores and distributes colony resources.
Acts as the central logistics hub.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from colony.buildings.base_building import BaseBuilding

from colony.resources.power import Power
from colony.resources.water import Water
from colony.resources.food import Food
from colony.resources.oxygen import Oxygen
from colony.resources.minerals import Minerals

# ============================================================
# Storage Facility
# ============================================================


@dataclass
class StorageFacility(BaseBuilding):

    building_id: int = 0

    name: str = "Storage Facility"

    position: tuple[int, int] = (0, 0)

    level: int = 1

    description: str = "Stores, organizes and distributes colony resources."

    storage_efficiency: float = 1.0

    transfer_rate: float = 100.0

    power_required: float = 6.0

    automation_level: float = 1.0

    inventory_accuracy: float = 100.0

    power: Power = field(
        default_factory=Power,
    )

    water: Water = field(
        default_factory=Water,
    )

    food: Food = field(
        default_factory=Food,
    )

    oxygen: Oxygen = field(
        default_factory=Oxygen,
    )

    minerals: Minerals = field(
        default_factory=Minerals,
    )

    total_resources_transferred: float = 0.0

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        if not self.operational:

            return

        self.manage_inventory()

        self.update_integrity()

    # ========================================================
    # Integrity
    # ========================================================

    def update_integrity(
        self,
    ) -> None:

        self.efficiency = self.health_percentage / 100.0

        self.inventory_accuracy = min(
            100.0,
            self.inventory_accuracy,
        )

    # ========================================================
    # Inventory
    # ========================================================

    def manage_inventory(
        self,
    ) -> float:

        if not self.operational or self.power.current_amount < self.power_required:

            return 0.0

        self.power.consume(
            self.power_required,
        )

        transferred = (
            self.transfer_rate
            * self.storage_efficiency
            * self.automation_level
            * self.efficiency
            * (self.inventory_accuracy / 100.0)
        )

        self.total_resources_transferred += transferred

        return transferred

    # ========================================================
    # Storage Management
    # ========================================================

    def repair_inventory_system(
        self,
        amount: float = 5.0,
    ) -> None:

        self.inventory_accuracy = min(
            100.0,
            self.inventory_accuracy + amount,
        )

    def inventory_corruption(
        self,
        amount: float = 5.0,
    ) -> None:

        self.inventory_accuracy = max(
            0.0,
            self.inventory_accuracy - amount,
        )

    def improve_automation(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.automation_level = min(
            2.0,
            self.automation_level + bonus,
        )

    def improve_storage(
        self,
        bonus: float = 0.05,
    ) -> None:

        self.storage_efficiency = min(
            2.0,
            self.storage_efficiency + bonus,
        )

    def increase_transfer_rate(
        self,
        amount: float = 10.0,
    ) -> None:

        self.transfer_rate += amount

    # ========================================================
    # Status
    # ========================================================

    @property
    def effective_transfer_rate(
        self,
    ) -> float:

        return (
            self.transfer_rate
            * self.storage_efficiency
            * self.automation_level
            * self.efficiency
            * (self.inventory_accuracy / 100.0)
        )

    @property
    def power_efficiency(
        self,
    ) -> float:

        if self.power_required <= 0:

            return 0.0

        return self.effective_transfer_rate / self.power_required

    @property
    def requires_maintenance(
        self,
    ) -> bool:

        return self.inventory_accuracy < 65.0

    @property
    def highly_automated(
        self,
    ) -> bool:

        return self.automation_level >= 1.5

    @property
    def fully_operational(
        self,
    ) -> bool:

        return self.operational and self.inventory_accuracy >= 95.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "storage_efficiency": round(
                    self.storage_efficiency,
                    2,
                ),
                "transfer_rate": round(
                    self.transfer_rate,
                    2,
                ),
                "effective_transfer_rate": round(
                    self.effective_transfer_rate,
                    2,
                ),
                "power_required": round(
                    self.power_required,
                    2,
                ),
                "automation_level": round(
                    self.automation_level,
                    2,
                ),
                "inventory_accuracy": round(
                    self.inventory_accuracy,
                    2,
                ),
                "power_efficiency": round(
                    self.power_efficiency,
                    2,
                ),
                "requires_maintenance": self.requires_maintenance,
                "highly_automated": self.highly_automated,
                "fully_operational": self.fully_operational,
                "total_resources_transferred": round(
                    self.total_resources_transferred,
                    2,
                ),
                "power": self.power.statistics(),
                "water": self.water.statistics(),
                "food": self.food.statistics(),
                "oxygen": self.oxygen.statistics(),
                "minerals": self.minerals.statistics(),
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "StorageFacility("
            f"health={self.health_percentage:.1f}%, "
            f"automation={self.automation_level:.2f}x, "
            f"transfer={self.effective_transfer_rate:.2f} kg/h, "
            f"accuracy={self.inventory_accuracy:.1f}%"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

Warehouse = StorageFacility
