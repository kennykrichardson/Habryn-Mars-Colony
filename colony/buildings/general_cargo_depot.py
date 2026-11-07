"""Fallback facility for resources without a dedicated storage class."""
from dataclasses import dataclass

from colony.buildings.storage_facility import StorageFacility


@dataclass
class GeneralCargoDepot(StorageFacility):
    name: str = "General Cargo Depot"
    description: str = "Finite fallback depot for approved miscellaneous cargo."
