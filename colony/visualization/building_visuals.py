"""Central visual identity metadata for every constructible facility."""
from __future__ import annotations


# Colours use the same compact pixel-art palette as pixel_art.py. Each entry
# names a silhouette family so renderer code can share drawing primitives.
BUILDING_VISUALS: dict[str, dict[str, object]] = {
    "Greenhouse": {"primary": "green", "secondary": "glass", "accent": "cream", "silhouette": "greenhouse"},
    "WaterReservoir": {"primary": "blue", "secondary": "metal", "accent": "cyan", "silhouette": "tank"},
    "WaterPlant": {"primary": "blue", "secondary": "metal", "accent": "cyan", "silhouette": "processing"},
    "FuelDepot": {"primary": "amber", "secondary": "metal", "accent": "red", "silhouette": "tank"},
    "OxygenStorageFacility": {"primary": "cyan", "secondary": "cream", "accent": "white", "silhouette": "cylinders"},
    "OxygenGenerator": {"primary": "cyan", "secondary": "metal", "accent": "white", "silhouette": "processing"},
    "Habitat": {"primary": "cream", "secondary": "glass", "accent": "amber", "silhouette": "habitat"},
    "MedicalBay": {"primary": "white", "secondary": "cream", "accent": "red", "silhouette": "medical"},
    "Laboratory": {"primary": "blue", "secondary": "glass", "accent": "cyan", "silhouette": "laboratory"},
    "Reactor": {"primary": "red", "secondary": "metal", "accent": "amber", "silhouette": "reactor"},
    "SolarArray": {"primary": "blue", "secondary": "metal", "accent": "cyan", "silhouette": "solar"},
    "Mine": {"primary": "red", "secondary": "metal", "accent": "amber", "silhouette": "mine"},
    "Workshop": {"primary": "metal", "secondary": "cream", "accent": "amber", "silhouette": "workshop"},
    "MaterialsWarehouse": {"primary": "metal", "secondary": "rock", "accent": "amber", "silhouette": "warehouse"},
    "FoodWarehouse": {"primary": "green", "secondary": "cream", "accent": "amber", "silhouette": "warehouse"},
    "GeneralCargoDepot": {"primary": "metal", "secondary": "cream", "accent": "cyan", "silhouette": "warehouse"},
    "StorageFacility": {"primary": "metal", "secondary": "cream", "accent": "amber", "silhouette": "warehouse"},
    "CommunicationsCenter": {"primary": "white", "secondary": "metal", "accent": "cyan", "silhouette": "communications"},
    "LaunchPad": {"primary": "metal", "secondary": "shadow", "accent": "amber", "silhouette": "launch"},
    "RecyclingPlant": {"primary": "green", "secondary": "metal", "accent": "cyan", "silhouette": "processing"},
    "Battery": {"primary": "metal", "secondary": "cream", "accent": "amber", "silhouette": "battery"},
}

DEFAULT_VISUAL = {"primary": "cream", "secondary": "metal", "accent": "amber", "silhouette": "habitat"}


def building_visual(kind: str) -> dict[str, object]:
    """Return the stable visual identity for a building class/name."""
    return BUILDING_VISUALS.get(kind, DEFAULT_VISUAL)
