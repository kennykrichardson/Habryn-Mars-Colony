"""Crisp low-resolution world renderer for immutable Habryn snapshots."""
from __future__ import annotations

import math

import pygame

from colony.visualization.pixel_art import (
    PALETTE,
    TERRAIN_COLORS,
    building_sprite,
    character_sprite,
    deposit_marker,
    terrain_tile,
)


class Camera:
    """World-space camera. Coordinates returned are in low-resolution pixels."""

    def __init__(self, tile_size: int = 16):
        self.tile_size = tile_size
        self.zoom = 1.25
        self.x = 0.0
        self.y = 0.0

    @property
    def cell(self) -> float:
        return self.tile_size * self.zoom

    def world_to_screen(self, position: tuple[float, float]) -> tuple[int, int]:
        return round((position[0] - self.x) * self.cell), round((position[1] - self.y) * self.cell)

    def screen_to_world(self, position: tuple[float, float]) -> tuple[float, float]:
        return position[0] / self.cell + self.x, position[1] / self.cell + self.y

    def zoom_at(self, factor: float, point: tuple[int, int], pixel_scale: int = 2) -> None:
        logical_point = (point[0] / pixel_scale, point[1] / pixel_scale)
        before = self.screen_to_world(logical_point)
        self.zoom = min(2.5, max(.55, self.zoom * factor))
        after = self.screen_to_world(logical_point)
        self.x += before[0] - after[0]
        self.y += before[1] - after[1]

    def center_on(self, position: tuple[float, float], logical_size: tuple[int, int]) -> None:
        self.x = position[0] - logical_size[0] / (2 * self.cell)
        self.y = position[1] - logical_size[1] / (2 * self.cell)


class Renderer:
    """Renderer consumes snapshots only; all effects and animation are cosmetic."""

    pixel_scale = 2

    def __init__(self, screen: pygame.Surface, camera: Camera | None = None, seed: int | None = 42):
        self.screen = screen
        self.camera = camera or Camera()
        self.bubble_font = pygame.font.SysFont("monospace", 12, bold=True)
        self.selected: tuple[str, object] | None = None
        self.last_snapshot = None
        self.seed = seed or 0
        self.show_grid = False
        self.show_exploration = True
        self.show_minimap = True
        self.last_world_surface_size = (0, 0)
        self._scaled_tiles: dict[tuple, pygame.Surface] = {}
        self._scaled_people: dict[tuple, pygame.Surface] = {}
        self._scaled_buildings: dict[tuple, pygame.Surface] = {}
        self._last_agent_directions: dict[object, int] = {}
        self._turn_started: dict[object, float] = {}

    def _tile_image(self, terrain, x, y, explored, platform, size):
        key = (terrain, x, y, explored, platform, size)
        image = self._scaled_tiles.get(key)
        if image is None:
            base = terrain_tile(terrain, x, y, self.seed, explored, platform)
            image = base if size == 16 else pygame.transform.scale(base, (size, size))
            if len(self._scaled_tiles) > 10000:
                self._scaled_tiles.clear()
            self._scaled_tiles[key] = image
        return image

    def _person_image(self, robot, frame, direction, activity, appearance, size):
        size = tuple(size)
        appearance_key = tuple(sorted((key, self._freeze(value)) for key, value in appearance.items()))
        key = (robot, frame, direction, activity, appearance_key, size)
        image = self._scaled_people.get(key)
        if image is None:
            source = character_sprite(robot, frame, direction, activity not in {"idle", "sleeping"},
                                      appearance, activity)
            image = pygame.transform.scale(source, size)
            self._scaled_people[key] = image
        return image

    @staticmethod
    def _freeze(value):
        if isinstance(value, (tuple, list)):
            return tuple(Renderer._freeze(item) for item in value)
        return value

    def _building_image(self, kind, width, height, online, damaged):
        key = (kind, width, height, online, damaged)
        image = self._scaled_buildings.get(key)
        if image is None:
            image = building_sprite(kind, width, height, online, damaged)
            if len(self._scaled_buildings) > 512:
                self._scaled_buildings.clear()
            self._scaled_buildings[key] = image
        return image

    def draw(self, snapshot, viewport: pygame.Rect) -> None:
        """Render the world at half resolution, then enlarge with nearest-neighbor."""
        self.last_snapshot = snapshot
        scale = self.pixel_scale
        logical_w = max(1, math.ceil(viewport.width / scale))
        logical_h = max(1, math.ceil(viewport.height / scale))
        self.last_world_surface_size = (logical_w, logical_h)
        world = pygame.Surface((logical_w, logical_h))
        world.fill(PALETTE["void"])
        cell = max(1, round(self.camera.cell))
        now = pygame.time.get_ticks() / 1000.0

        for x, y, terrain, explored, occupied, deposits in snapshot.tiles:
            sx, sy = self.camera.world_to_screen((x, y))
            if sx + cell <= 0 or sy + cell <= 0 or sx >= logical_w or sy >= logical_h:
                continue
            reveal = explored if self.show_exploration else True
            tile = self._tile_image(terrain, x, y, reveal, occupied, cell)
            world.blit(tile, (sx, sy))
            if self.show_grid and cell >= 10:
                pygame.draw.rect(world, (52, 38, 38), (sx, sy, cell, cell), 1)
            if deposits and cell >= 8 and reveal:
                marker = deposit_marker(deposits[0][0], max(5, min(9, cell // 2)))
                world.blit(marker, (sx + cell - marker.get_width() - 2, sy + 2))

        # Every building comes from the unique entity registry, so a multi-tile
        # footprint is rendered once using its authoritative dimensions.
        for building in snapshot.buildings:
            x, y = building["position"]
            sx, sy = self.camera.world_to_screen((x, y))
            fw, fh = building.get("footprint", (1, 1))
            width, height = max(8, round(cell * fw)), max(8, round(cell * fh))
            integrity = building.get("integrity", 100)
            damaged = integrity is not None and integrity < 60
            online = bool(building.get("enabled", True)) and integrity != 0
            if building.get("powered") is False:
                online = False
            sprite = self._building_image(building.get("category", building.get("name", "Habitat")),
                                          width, height, online, damaged)
            world.blit(sprite, (sx, sy))
            if self.selected == ("building", building["id"]):
                pygame.draw.rect(world, PALETTE["amber"], (sx - 1, sy - 1, width + 2, height + 2), 1)

        for agent in snapshot.agents:
            x, y = agent["position"]
            sx, sy = self.camera.world_to_screen((x, y))
            moving = bool(agent.get("moving", False))
            state = str(agent.get("state", "")).lower()
            activity = str(agent.get("current_activity", "idle")).lower()
            if activity in {"idle", ""}:
                activity = state
            if moving:
                activity = "walking"
            elif agent.get("busy") and activity in {"idle", "working"}:
                activity = "working"
            destination = agent.get("destination")
            direction = 1
            if destination:
                dx, dy = destination[0] - x, destination[1] - y
                if abs(dy) > abs(dx):
                    direction = 0 if dy < 0 else 2
                else:
                    direction = 3 if dx < 0 else 1
            previous_direction = self._last_agent_directions.get(agent["id"])
            if moving and previous_direction is not None and direction != previous_direction:
                self._turn_started[agent["id"]] = now
            self._last_agent_directions[agent["id"]] = direction
            if agent["id"] in self._turn_started and now - self._turn_started[agent["id"]] < .25:
                activity = "turning"
            frame = int(now * (7 if activity in {"walking", "turning"} else 4)) % 4
            robot = agent.get("category") == "robot"
            height = max(9, round(cell * (1.15 if robot else 1.32)))
            width = max(8, round(height * (1.12 if robot else .75)))
            width = min(width, max(8, round(cell * 1.04)))
            character = self._person_image(robot, frame, direction, activity,
                                           agent.get("appearance", {}), (width, height))
            px = sx + (cell - width) // 2
            py = sy + cell - height
            world.blit(character, (px, py))
            if self.selected == ("agent", agent["id"]):
                pygame.draw.rect(world, PALETTE["amber"], (sx + 1, sy + 1, cell - 2, cell - 2), 1)

        self._draw_dust(world, logical_w, logical_h, now)
        enlarged = pygame.transform.scale(world, (viewport.width, viewport.height))
        self.screen.blit(enlarged, viewport.topleft)
        self._draw_conversation_bubbles(snapshot, viewport, cell, now)
        if self.show_minimap:
            self._draw_minimap(snapshot, viewport)

    def _draw_conversation_bubbles(self, snapshot, viewport, cell: int, now: float) -> None:
        conversations = snapshot.telemetry.get("active_conversations", ())
        if not conversations:
            return
        conversation = conversations[-1]
        agents = {agent["id"]: agent for agent in snapshot.agents}
        latest_turns = {}
        for turn in conversation.get("turns", ()):
            latest_turns[turn["speaker_id"]] = turn
        for speaker_id, turn in list(latest_turns.items())[-2:]:
            agent = agents.get(speaker_id)
            if agent is None:
                continue
            x, y = agent["position"]
            sx, sy = self.camera.world_to_screen((x + .5, y))
            anchor = (viewport.x + sx * self.pixel_scale,
                      viewport.y + sy * self.pixel_scale - round(cell * self.pixel_scale * 1.15))
            if not viewport.collidepoint(anchor):
                continue
            text = str(turn.get("text", ""))
            max_width = min(230, viewport.width - 12)
            while text and self.bubble_font.size(text)[0] > max_width - 14:
                text = text[:-2] + "…" if len(text) > 2 else text[:-1]
            text_surface = self.bubble_font.render(text, False, (45, 37, 36))
            bubble_width = min(max_width, text_surface.get_width() + 14)
            bubble_height = 25
            bx = max(viewport.left + 5, min(viewport.right - bubble_width - 5, anchor[0] - bubble_width // 2))
            by = max(viewport.top + 5, anchor[1] - bubble_height - 6)
            color = tuple(agent.get("appearance", {}).get("trim_color", PALETTE["cream"]))
            pygame.draw.rect(self.screen, (38, 30, 31), (bx - 2, by - 2, bubble_width + 4, bubble_height + 4))
            pygame.draw.rect(self.screen, (235, 219, 181), (bx, by, bubble_width, bubble_height))
            pygame.draw.rect(self.screen, color, (bx, by, bubble_width, 3))
            pygame.draw.polygon(self.screen, (235, 219, 181),
                                [(anchor[0] - 4, by + bubble_height),
                                 (anchor[0] + 4, by + bubble_height), (anchor[0], by + bubble_height + 5)])
            self.screen.blit(text_surface, (bx + 7, by + 6))

    def _draw_dust(self, target: pygame.Surface, width: int, height: int, now: float) -> None:
        # A few smooth, deterministic particles drift across the map layer only.
        for i in range(7):
            x = int((i * 97 + now * (3 + i % 3) * 7) % max(1, width))
            y = int((i * 53 + math.sin(now * .35 + i) * 9) % max(1, height))
            target.set_at((x, y), (185, 117, 84))
            if i % 3 == 0 and x + 1 < width:
                target.set_at((x + 1, y), (153, 94, 73))

    def _draw_minimap(self, snapshot, viewport: pygame.Rect) -> None:
        width, height = 132, 92
        x, y = viewport.left + 12, viewport.bottom - height - 12
        if x + width > viewport.right - 8 or y < viewport.top + 60:
            return
        minimap = pygame.Surface((width, height))
        minimap.fill((33, 28, 31))
        map_rect = pygame.Rect(4, 4, width - 8, height - 8)
        for tx, ty, terrain, explored, _occupied, _deposits in snapshot.tiles:
            px = map_rect.x + tx * map_rect.width // snapshot.width
            py = map_rect.y + ty * map_rect.height // snapshot.height
            color = TERRAIN_COLORS.get(terrain, PALETTE["soil"])
            if not explored:
                color = tuple(c // 2 for c in color)
            minimap.set_at((px, py), color)
        for building in snapshot.buildings:
            bx, by = building["position"]
            px = map_rect.x + bx * map_rect.width // snapshot.width
            py = map_rect.y + by * map_rect.height // snapshot.height
            minimap.set_at((px, py), PALETTE["cyan"])
        for agent in snapshot.agents:
            ax, ay = agent["position"]
            px = map_rect.x + ax * map_rect.width // snapshot.width
            py = map_rect.y + ay * map_rect.height // snapshot.height
            minimap.set_at((px, py), PALETTE["amber"] if agent["category"] == "agent" else PALETTE["cyan"])
        pygame.draw.rect(minimap, PALETTE["cream"], map_rect, 1)
        pygame.draw.rect(minimap, PALETTE["amber"], (0, 0, width, height), 2)
        self.screen.blit(minimap, (x, y))

    def minimap_rect(self, viewport: pygame.Rect) -> pygame.Rect | None:
        rect = pygame.Rect(viewport.left + 12, viewport.bottom - 104, 132, 92)
        if not self.show_minimap or rect.right > viewport.right - 8 or rect.top < viewport.top + 60:
            return None
        return rect

    def center_from_minimap(self, snapshot, point: tuple[int, int], viewport: pygame.Rect) -> bool:
        rect = self.minimap_rect(viewport)
        if rect is None or not rect.collidepoint(point):
            return False
        map_rect = pygame.Rect(rect.x + 4, rect.y + 4, rect.width - 8, rect.height - 8)
        wx = (point[0] - map_rect.x) * snapshot.width / map_rect.width
        wy = (point[1] - map_rect.y) * snapshot.height / map_rect.height
        self.camera.center_on((wx, wy), (viewport.width // self.pixel_scale, viewport.height // self.pixel_scale))
        return True

    def pick(self, snapshot, screen_position: tuple[int, int], viewport: pygame.Rect):
        """Resolve the actual world cell under the pointer at every zoom level."""
        if not viewport.collidepoint(screen_position):
            return None
        rect = self.minimap_rect(viewport)
        if rect and rect.collidepoint(screen_position):
            return "minimap", {"position": screen_position}
        local = ((screen_position[0] - viewport.x) / self.pixel_scale,
                 (screen_position[1] - viewport.y) / self.pixel_scale)
        wx, wy = self.camera.screen_to_world(local)
        x, y = math.floor(wx), math.floor(wy)
        for entity in reversed(snapshot.agents):
            if tuple(entity["position"]) == (x, y):
                return "agent", entity
        for entity in reversed(snapshot.buildings):
            bx, by = entity["position"]
            fw, fh = entity.get("footprint", (1, 1))
            if bx <= x < bx + fw and by <= y < by + fh:
                return "building", entity
        tile = next((item for item in snapshot.tiles if item[0] == x and item[1] == y), None)
        if tile:
            return "tile", {"position": (x, y), "terrain": tile[2], "explored": tile[3],
                             "deposits": dict(tile[5])}
        return None
