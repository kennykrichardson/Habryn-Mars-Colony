"""Dedicated, finite-capacity destination for the colony Fuel inventory."""
from dataclasses import dataclass
from typing import ClassVar

from colony.buildings.storage_facility import StorageFacility


@dataclass
class FuelDepot(StorageFacility):
    name: str = "Fuel Depot"
    description: str = "Safety-rated depot for the colony's authoritative fuel stock."
    accepted_resource_names: ClassVar[frozenset[str]] = frozenset({"Fuel"})
    minimum_reserve: float = 250.0
    target_reserve: float = 500.0
    emergency_reserve: float = 100.0
    maximum_stock: float = 800.0
