"""Dedicated destination for the authoritative Minerals inventory."""
from dataclasses import dataclass
from typing import ClassVar

from colony.buildings.storage_facility import StorageFacility


@dataclass
class MaterialsWarehouse(StorageFacility):
    name: str = "Materials Warehouse"
    description: str = "Finite warehouse for processed construction minerals."
    accepted_resource_names: ClassVar[frozenset[str]] = frozenset({"Minerals"})
    minimum_reserve: float = 200.0
    target_reserve: float = 600.0
    emergency_reserve: float = 60.0
    maximum_stock: float = 5000.0
