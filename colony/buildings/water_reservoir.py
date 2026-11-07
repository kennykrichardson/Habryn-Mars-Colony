"""Dedicated destination for the authoritative Water inventory."""
from dataclasses import dataclass
from typing import ClassVar

from colony.buildings.storage_facility import StorageFacility


@dataclass
class WaterReservoir(StorageFacility):
    name: str = "Water Reservoir"
    description: str = "Finite reservoir for the colony's shared water inventory."
    accepted_resource_names: ClassVar[frozenset[str]] = frozenset({"Water"})
    minimum_reserve: float = 400.0
    target_reserve: float = 800.0
    emergency_reserve: float = 120.0
    maximum_stock: float = 3000.0
