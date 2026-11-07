"""Dedicated destination for the authoritative Oxygen inventory."""
from dataclasses import dataclass
from typing import ClassVar

from colony.buildings.storage_facility import StorageFacility


@dataclass
class OxygenStorageFacility(StorageFacility):
    name: str = "Oxygen Storage"
    description: str = "Finite pressure-rated store for the colony's shared oxygen inventory."
    accepted_resource_names: ClassVar[frozenset[str]] = frozenset({"Oxygen"})
    minimum_reserve: float = 400.0
    target_reserve: float = 900.0
    emergency_reserve: float = 150.0
    maximum_stock: float = 2500.0
