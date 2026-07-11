"""
terrain.py

Part 1/4

Canonical terrain definitions for Habryn.

Provides terrain types and helper methods used by

- MarsMap
- Pathfinding
- Construction
- Mining
- Exploration

Terrain objects are immutable descriptors.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ============================================================
# Terrain
# ============================================================


@dataclass(slots=True)
class Terrain:

    name: str

    walkable: bool = True

    movement_cost: float = 1.0

    buildable: bool = True

    mineable: bool = False

    radiation: float = 0.0

    elevation: float = 0.0

    color: str = "#888888"

    metadata: dict = field(default_factory=dict)

    # ========================================================
    # Metadata
    # ========================================================

    def set_metadata(
        self,
        key: str,
        value,
    ) -> None:

        self.metadata[key] = value

    def get_metadata(
        self,
        key: str,
        default=None,
    ):

        return self.metadata.get(
            key,
            default,
        )


# ============================================================
# Canonical Terrain Library
# ============================================================


PLAINS = Terrain(
    name="Plains",
    movement_cost=1.0,
    buildable=True,
)

ROCK = Terrain(
    name="Rock",
    movement_cost=1.5,
    mineable=True,
)

SAND = Terrain(
    name="Sand",
    movement_cost=2.0,
)

CLIFF = Terrain(
    name="Cliff",
    walkable=False,
    buildable=False,
)

ICE = Terrain(
    name="Ice",
    movement_cost=1.3,
    mineable=True,
)

CRATER = Terrain(
    name="Crater",
    movement_cost=2.5,
)

LAVA_TUBE = Terrain(
    name="Lava Tube",
    movement_cost=1.2,
    buildable=True,
)

TERRAIN_LIBRARY = {
    terrain.name.lower(): terrain
    for terrain in (
        PLAINS,
        ROCK,
        SAND,
        CLIFF,
        ICE,
        CRATER,
        LAVA_TUBE,
    )
}


# ============================================================
# Lookup
# ============================================================


def get_terrain(
    name: str,
) -> Terrain:

    return TERRAIN_LIBRARY[name.lower()]


# ============================================================
# Queries
# ============================================================


def walkable_terrains() -> list[Terrain]:

    return [terrain for terrain in TERRAIN_LIBRARY.values() if terrain.walkable]


def buildable_terrains() -> list[Terrain]:

    return [terrain for terrain in TERRAIN_LIBRARY.values() if terrain.buildable]


def mineable_terrains() -> list[Terrain]:

    return [terrain for terrain in TERRAIN_LIBRARY.values() if terrain.mineable]


# ============================================================
# Registration
# ============================================================


def register_terrain(
    terrain: Terrain,
) -> None:

    TERRAIN_LIBRARY[terrain.name.lower()] = terrain


def unregister_terrain(
    name: str,
) -> None:

    TERRAIN_LIBRARY.pop(
        name.lower(),
        None,
    )


# ============================================================
# Statistics
# ============================================================


def statistics() -> dict:

    return {
        "terrain_types": len(
            TERRAIN_LIBRARY,
        ),
        "walkable": len(
            walkable_terrains(),
        ),
        "buildable": len(
            buildable_terrains(),
        ),
        "mineable": len(
            mineable_terrains(),
        ),
    }


# ============================================================
# Utility
# ============================================================


def terrain_exists(
    name: str,
) -> bool:

    return name.lower() in TERRAIN_LIBRARY


def all_terrains() -> list[Terrain]:

    return list(
        TERRAIN_LIBRARY.values(),
    )


def names() -> list[str]:

    return sorted(TERRAIN_LIBRARY.keys())


# ============================================================
# Serialization
# ============================================================


def serialize() -> dict:

    return {
        name: {
            "walkable": terrain.walkable,
            "movement_cost": terrain.movement_cost,
            "buildable": terrain.buildable,
            "mineable": terrain.mineable,
            "radiation": terrain.radiation,
            "elevation": terrain.elevation,
            "color": terrain.color,
            "metadata": dict(
                terrain.metadata,
            ),
        }
        for name, terrain in TERRAIN_LIBRARY.items()
    }


def deserialize(
    data: dict,
) -> None:

    TERRAIN_LIBRARY.clear()

    for name, values in data.items():

        TERRAIN_LIBRARY[name] = Terrain(
            name=name.title(),
            walkable=values.get(
                "walkable",
                True,
            ),
            movement_cost=values.get(
                "movement_cost",
                1.0,
            ),
            buildable=values.get(
                "buildable",
                True,
            ),
            mineable=values.get(
                "mineable",
                False,
            ),
            radiation=values.get(
                "radiation",
                0.0,
            ),
            elevation=values.get(
                "elevation",
                0.0,
            ),
            color=values.get(
                "color",
                "#888888",
            ),
            metadata=dict(
                values.get(
                    "metadata",
                    {},
                )
            ),
        )


# ============================================================
# Aliases
# ============================================================

TerrainType = Terrain

TerrainRegistry = TERRAIN_LIBRARY

DEFAULT_TERRAIN = PLAINS
