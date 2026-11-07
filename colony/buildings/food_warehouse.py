"""Dedicated destination for the authoritative Food inventory."""
from dataclasses import dataclass
from typing import ClassVar

from colony.buildings.storage_facility import StorageFacility


@dataclass
class FoodWarehouse(StorageFacility):
    name: str = "Food Warehouse"
    description: str = "Finite warehouse for the colony's shared food inventory."
    accepted_resource_names: ClassVar[frozenset[str]] = frozenset({"Food"})
    minimum_reserve: float = 300.0
    target_reserve: float = 600.0
    emergency_reserve: float = 100.0
    maximum_stock: float = 1800.0
