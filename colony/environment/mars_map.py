"""
mars_map.py

Part 1/5

Canonical Mars map implementation.

Owns

- map dimensions
- terrain tiles
- occupancy
- building placement
- agent positions

Does NOT perform pathfinding.

The pathfinding system will consume this map.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from typing import Any

from colony.environment.terrain import (
    Terrain,
    DEFAULT_TERRAIN,
)

# ============================================================
# Map Tile
# ============================================================


@dataclass(slots=True)
class MapTile:

    x: int

    y: int

    terrain: Terrain = field(
        default_factory=lambda: DEFAULT_TERRAIN,
    )

    walkable: bool = True

    occupied: bool = False

    explored: bool = False

    elevation: float = 0.0

    resource_deposit: dict[
        str,
        float,
    ] = field(
        default_factory=dict,
    )

    radiation: float = 0.0

    temperature: float = -60.0

    hazard_level: float = 0.0

    region: str = "Unknown"

    building: Any | None = None

    building_origin: tuple[int, int] | None = None

    local_x: int = 0

    local_y: int = 0

    agents: list[Any] = field(
        default_factory=list,
    )


# ============================================================
# Mars Map
# ============================================================


@dataclass
class MarsMap:

    width: int = 100

    height: int = 100

    tiles: dict[
        tuple[int, int],
        MapTile,
    ] = field(default_factory=dict)

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        for y in range(self.height):

            for x in range(self.width):

                self.tiles[(x, y)] = MapTile(
                    x=x,
                    y=y,
                )

    # ========================================================
    # Tile Access
    # ========================================================

    def get_tile(
        self,
        x: int,
        y: int,
    ) -> MapTile | None:

        return self.tiles.get(
            (x, y),
        )

    def in_bounds(
        self,
        x: int,
        y: int,
    ) -> bool:

        return 0 <= x < self.width and 0 <= y < self.height

    # ========================================================
    # Terrain
    # ========================================================

    def set_terrain(
        self,
        x: int,
        y: int,
        terrain: Terrain,
    ) -> None:

        tile = self.get_tile(
            x,
            y,
        )

        if tile is None:

            return

        tile.terrain = terrain

        tile.walkable = terrain.walkable

    # ========================================================
    # Resources
    # ========================================================

    def add_resource(
        self,
        x: int,
        y: int,
        resource: str,
        amount: float,
    ) -> None:

        tile = self.get_tile(
            x,
            y,
        )

        if tile is None:

            return

        tile.resource_deposit[resource] = (
            tile.resource_deposit.get(
                resource,
                0.0,
            )
            + amount
        )

    def remove_resource(
        self,
        x: int,
        y: int,
        resource: str,
        amount: float,
    ) -> float:

        tile = self.get_tile(
            x,
            y,
        )

        if tile is None:

            return 0.0

        available = tile.resource_deposit.get(
            resource,
            0.0,
        )

        removed = min(
            available,
            amount,
        )

        remaining = available - removed

        if remaining <= 0.0:

            tile.resource_deposit.pop(
                resource,
                None,
            )

        else:

            tile.resource_deposit[resource] = remaining

        return removed

    def resource_amount(
        self,
        x: int,
        y: int,
        resource: str,
    ) -> float:

        tile = self.get_tile(
            x,
            y,
        )

        if tile is None:

            return 0.0

        return tile.resource_deposit.get(
            resource,
            0.0,
        )

    def has_resource(
        self,
        x: int,
        y: int,
        resource: str,
    ) -> bool:

        return (
            self.resource_amount(
                x,
                y,
                resource,
            )
            > 0.0
        )

    def set_walkable(
        self,
        x: int,
        y: int,
        value: bool,
    ) -> None:

        tile = self.get_tile(
            x,
            y,
        )

        if tile is not None:

            tile.walkable = value

    # ========================================================
    # Buildings
    # ========================================================

    def place_building(
        self,
        building: Any,
        origin: tuple[int, int],
        width: int | None = None,
        height: int | None = None,
    ) -> bool:

        ox, oy = origin
        default_width, default_height = type(building).default_footprint
        width = default_width if width is None else width
        height = default_height if height is None else height

        if width <= 0 or height <= 0:
            return False

        # Validate footprint

        for dy in range(height):

            for dx in range(width):

                x = ox + dx

                y = oy + dy

                if not self.in_bounds(
                    x,
                    y,
                ):

                    return False

                tile = self.get_tile(
                    x,
                    y,
                )

                if tile is None:

                    return False

                if not tile.terrain.buildable:
                    return False

                if tile.occupied:

                    return False

                if tile.agents:
                    return False

        # Place footprint

        for dy in range(height):

            for dx in range(width):

                tile = self.get_tile(
                    ox + dx,
                    oy + dy,
                )

                assert tile is not None

                tile.building = building

                tile.building_origin = origin

                tile.local_x = dx

                tile.local_y = dy

                tile.occupied = True

                tile.walkable = False

        return True

    def remove_building(
        self,
        position: tuple[int, int],
    ) -> None:

        tile = self.get_tile(
            *position,
        )

        if tile is None:

            return

        if tile.building is None:

            return

        origin = tile.building_origin

        building = tile.building

        for current in self.tiles.values():

            if current.building != building:

                continue

            if current.building_origin != origin:

                continue

            current.building = None

            current.building_origin = None

            current.local_x = 0

            current.local_y = 0

            current.occupied = False

            current.walkable = current.terrain.walkable

    # ========================================================
    # Agents
    # ========================================================

    def add_agent(
        self,
        agent: Any,
        position: tuple[int, int],
    ) -> bool:

        tile = self.get_tile(
            *position,
        )

        if tile is None:

            return False

        if not tile.walkable or tile.building is not None:
            return False

        if agent not in tile.agents:

            tile.agents.append(
                agent,
            )

        return True

    def remove_agent(
        self,
        agent: Any,
        position: tuple[int, int],
    ) -> None:

        tile = self.get_tile(
            *position,
        )

        if tile is None:

            return

        if agent in tile.agents:

            tile.agents.remove(
                agent,
            )

    def move_agent(
        self,
        agent: Any,
        source: tuple[int, int],
        destination: tuple[int, int],
    ) -> bool:

        if not self.in_bounds(
            *destination,
        ):

            return False

        destination_tile = self.get_tile(
            *destination,
        )

        if destination_tile is None or not destination_tile.walkable:

            return False

        source_tile = self.get_tile(*source)
        if source_tile is None or agent not in source_tile.agents:
            return False

        self.remove_agent(
            agent,
            source,
        )

        self.add_agent(
            agent,
            destination,
        )

        return True

    # ========================================================
    # Exploration
    # ========================================================

    def explore(
        self,
        x: int,
        y: int,
    ) -> None:

        tile = self.get_tile(
            x,
            y,
        )

        if tile is not None:

            tile.explored = True

    def explored_tiles(
        self,
    ) -> list[MapTile]:

        return [tile for tile in self.tiles.values() if tile.explored]

        # ========================================================

    # Queries
    # ========================================================

    def neighbors(
        self,
        x: int,
        y: int,
    ) -> list[MapTile]:

        neighbors: list[MapTile] = []

        directions = (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        )

        for dx, dy in directions:

            nx = x + dx

            ny = y + dy

            tile = self.get_tile(
                nx,
                ny,
            )

            if tile is not None:

                neighbors.append(
                    tile,
                )

        return neighbors

    def walkable_neighbors(
        self,
        x: int,
        y: int,
    ) -> list[MapTile]:

        return [
            tile
            for tile in self.neighbors(
                x,
                y,
            )
            if tile.walkable
        ]

    def occupied_tiles(
        self,
    ) -> list[MapTile]:

        return [tile for tile in self.tiles.values() if tile.occupied]

    def buildings(
        self,
    ) -> list[Any]:

        result = []
        seen = set()
        for tile in self.tiles.values():
            if tile.building is not None and id(tile.building) not in seen:
                result.append(tile.building)
                seen.add(id(tile.building))
        return result

    def agents(
        self,
    ) -> list[Any]:

        result: list[Any] = []

        for tile in self.tiles.values():

            result.extend(
                tile.agents,
            )

        return result

    @property
    def explored_percentage(
        self,
    ) -> float:

        if not self.tiles:

            return 0.0

        return (
            len(
                self.explored_tiles(),
            )
            / len(
                self.tiles,
            )
        ) * 100.0

    @property
    def occupancy_percentage(
        self,
    ) -> float:

        if not self.tiles:

            return 0.0

        return (
            len(
                self.occupied_tiles(),
            )
            / len(
                self.tiles,
            )
        ) * 100.0

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        return {
            "width": self.width,
            "height": self.height,
            "tiles": len(
                self.tiles,
            ),
            "occupied_tiles": len(
                self.occupied_tiles(),
            ),
            "explored_tiles": len(
                self.explored_tiles(),
            ),
            "buildings": len(
                self.buildings(),
            ),
            "agents": len(
                self.agents(),
            ),
        }

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        return {
            "width": self.width,
            "height": self.height,
            "tiles": {
                f"{x},{y}": {
                    "terrain": tile.terrain.name,
                    "walkable": tile.walkable,
                    "occupied": tile.occupied,
                    "explored": tile.explored,
                    "elevation": tile.elevation,
                    "radiation": tile.radiation,
                    "temperature": tile.temperature,
                    "hazard_level": tile.hazard_level,
                    "region": tile.region,
                    "resource_deposit": dict(
                        tile.resource_deposit,
                    ),
                }
                for (x, y), tile in self.tiles.items()
            },
        }

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "MarsMap":

        from colony.environment.terrain import (
            get_terrain,
        )

        mars_map = cls(
            width=data["width"],
            height=data["height"],
        )

        for key, values in data.get(
            "tiles",
            {},
        ).items():

            x, y = map(
                int,
                key.split(","),
            )

            tile = mars_map.get_tile(
                x,
                y,
            )

            if tile is None:

                continue

            terrain_name = values.get(
                "terrain",
                DEFAULT_TERRAIN.name,
            )

            tile.terrain = get_terrain(
                terrain_name,
            )

            tile.walkable = values.get(
                "walkable",
                tile.terrain.walkable,
            )

            tile.occupied = values.get(
                "occupied",
                False,
            )

            tile.explored = values.get(
                "explored",
                False,
            )

            tile.elevation = values.get(
                "elevation",
                0.0,
            )

            tile.radiation = values.get(
                "radiation",
                0.0,
            )

            tile.temperature = values.get(
                "temperature",
                -60.0,
            )

            tile.hazard_level = values.get(
                "hazard_level",
                0.0,
            )

            tile.region = values.get(
                "region",
                "Unknown",
            )

            tile.resource_deposit = dict(
                values.get(
                    "resource_deposit",
                    {},
                )
            )

        return mars_map

    # ========================================================
    # Utility
    # ========================================================

    def __getitem__(
        self,
        position: tuple[int, int],
    ) -> MapTile:

        return self.tiles[position]

    def __contains__(
        self,
        position: tuple[int, int],
    ) -> bool:

        return position in self.tiles

    def __repr__(
        self,
    ) -> str:

        return (
            "MarsMap("
            f"{self.width}x{self.height}, "
            f"tiles={len(self.tiles)}, "
            f"buildings={len(self.buildings())}, "
            f"agents={len(self.agents())}"
            ")"
        )
