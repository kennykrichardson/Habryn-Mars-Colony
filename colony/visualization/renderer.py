"""Native-resolution, quality-scalable renderer for immutable Habryn snapshots."""
from __future__ import annotations

import math
from time import perf_counter

import pygame

from colony.visualization.pixel_art import (
    PALETTE,
    TERRAIN_COLORS,
    building_sprite,
    character_sprite,
    deposit_marker,
    terrain_tile,
)
from colony.visualization.render_settings import QUALITY_PRESETS


class Camera:
    """World-space camera whose screen coordinates are native display pixels."""

    def __init__(self, tile_size: int = 32):
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

    def zoom_at(self, factor: float, point: tuple[int, int], pixel_scale: int = 1) -> None:
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
    """Native-resolution, presentation-only renderer over immutable snapshots."""

    pixel_scale = 1

    def __init__(self, screen: pygame.Surface, camera: Camera | None = None, seed: int | None = 42,
                 quality: str = "High", ui_scale: float = 1.0):
        if quality not in QUALITY_PRESETS:
            raise ValueError(f"Unknown rendering quality: {quality}")
        self.screen = screen
        self.camera = camera or Camera()
        self.quality = quality
        self.quality_options = QUALITY_PRESETS[quality]
        self.ui_scale = max(.75, min(3.0, ui_scale))
        self.bubble_font = pygame.font.SysFont("monospace", max(10, round(12 * self.ui_scale)), bold=True)
        self.selected: tuple[str, object] | None = None
        self.last_snapshot = None
        self.seed = seed or 0
        self.show_grid = False
        self.show_exploration = True
        self.show_minimap = True
        self.last_world_surface_size = (0, 0)
        self.last_frame_time_ms = 0.0
        self.last_draw_stats: dict[str, int] = {}
        self._scaled_tiles: dict[tuple, pygame.Surface] = {}
        self._terrain_chunks: dict[tuple, pygame.Surface] = {}
        self._chunk_scale: int | None = None
        self._chunk_render_key: tuple | None = None
        self._tile_coordinate_signature: tuple | None = None
        self._tile_indices_by_chunk: dict[tuple[int, int], tuple[int, ...]] = {}
        self._tile_group_signatures: dict[tuple[int, int], tuple] = {}
        self.chunk_size = 16
        self._scaled_people: dict[tuple, pygame.Surface] = {}
        self._scaled_buildings: dict[tuple, pygame.Surface] = {}
        self._last_agent_directions: dict[object, int] = {}
        self._turn_started: dict[object, float] = {}
        self._minimap_cache_key: tuple | None = None
        self._minimap_surface: pygame.Surface | None = None
        self.minimap_rebuild_count = 0

    def _tile_image(self, terrain, x, y, explored, platform, size):
        key = (terrain, x, y, explored, platform, size, self.quality)
        image = self._scaled_tiles.get(key)
        if image is None:
            base = terrain_tile(terrain, x, y, self.seed, explored, platform,
                                self.quality_options["terrain_size"], self.quality_options["terrain_detail"])
            image = base if base.get_size() == (size, size) else pygame.transform.scale(base, (size, size))
            if len(self._scaled_tiles) > 4096:
                self._scaled_tiles.clear()
            self._scaled_tiles[key] = image
        return image

    def _terrain_chunk(self, tiles, chunk_x: int, chunk_y: int, cell: int) -> pygame.Surface:
        x0, y0 = chunk_x * self.chunk_size, chunk_y * self.chunk_size
        width = min(self.chunk_size, max(0, self.last_snapshot.width - x0))
        height = min(self.chunk_size, max(0, self.last_snapshot.height - y0))
        key = (chunk_x, chunk_y, cell, self.quality, self.show_exploration, self.show_grid)
        cached = self._terrain_chunks.get(key)
        if cached is not None:
            return cached
        chunk = pygame.Surface((max(1, width * cell), max(1, height * cell)))
        chunk.fill(PALETTE["void"])
        for x, y, terrain, explored, occupied, deposits, _region in tiles:
            reveal = explored if self.show_exploration else True
            tile = self._tile_image(terrain, x, y, reveal, occupied, cell)
            px, py = (x - x0) * cell, (y - y0) * cell
            chunk.blit(tile, (px, py))
            if self.show_grid and cell >= 10:
                pygame.draw.rect(chunk, (52, 38, 38), (px, py, cell, cell), 1)
            if deposits and cell >= 8 and reveal:
                marker = deposit_marker(deposits[0][0], max(7, min(16, cell // 2)))
                chunk.blit(marker, (px + cell - marker.get_width() - 3, py + 3))
        if len(self._terrain_chunks) >= 128:
            self._terrain_chunks.clear()
        self._terrain_chunks[key] = chunk
        return chunk

    def _person_image(self, robot, frame, direction, activity, appearance, size):
        size = tuple(size)
        appearance_key = tuple(sorted((key, self._freeze(value)) for key, value in appearance.items()))
        detail = self.quality_options["sprite_detail"]
        key = (robot, frame, direction, activity, appearance_key, size, detail)
        image = self._scaled_people.get(key)
        if image is None:
            source = character_sprite(robot, frame, direction, activity not in {"idle", "sleeping"},
                                      appearance, activity, detail)
            image = pygame.transform.scale(source, size)
            self._scaled_people[key] = image
        return image

    @staticmethod
    def _freeze(value):
        if isinstance(value, (tuple, list)):
            return tuple(Renderer._freeze(item) for item in value)
        return value

    def _building_image(self, kind, width, height, online, damaged, status):
        detail = self.quality_options["sprite_detail"]
        key = (kind, width, height, online, damaged, status, detail)
        image = self._scaled_buildings.get(key)
        if image is None:
            image = building_sprite(kind, width, height, online, damaged, status, detail)
            if len(self._scaled_buildings) > 384:
                self._scaled_buildings.clear()
            self._scaled_buildings[key] = image
        return image

    def set_quality(self, quality: str) -> None:
        """Change presentation detail without mutating the simulation snapshot."""
        if quality not in QUALITY_PRESETS:
            raise ValueError(f"Unknown rendering quality: {quality}")
        if quality != self.quality:
            self.quality = quality
            self.quality_options = QUALITY_PRESETS[quality]
            self._scaled_tiles.clear()
            self._terrain_chunks.clear()
            self._scaled_people.clear()
            self._scaled_buildings.clear()

    def set_ui_scale(self, scale: float) -> None:
        self.ui_scale = max(.75, min(3.0, float(scale)))
        self.bubble_font = pygame.font.SysFont("monospace", max(10, round(12 * self.ui_scale)), bold=True)
        self._minimap_cache_key = None
        self._minimap_surface = None

    def draw(self, snapshot, viewport: pygame.Rect) -> None:
        """Draw directly to the selected display surface without a low-res world buffer."""
        frame_started = perf_counter()
        self.last_snapshot = snapshot
        self.last_world_surface_size = viewport.size
        self.screen.set_clip(viewport)
        self.screen.fill(PALETTE["void"], viewport)
        origin_x, origin_y = viewport.topleft
        logical_w, logical_h = viewport.size
        cell = max(1, round(self.camera.cell))
        now = pygame.time.get_ticks() / 1000.0
        visible_tiles = 0
        visible_buildings = 0
        visible_agents = 0

        render_key = (cell, self.quality, self.show_exploration, self.show_grid)
        if self._chunk_render_key != render_key:
            self._terrain_chunks.clear()
            self._chunk_render_key = render_key
            self._chunk_scale = cell
        coordinate_signature = tuple((tile[0], tile[1]) for tile in snapshot.tiles)
        if coordinate_signature != self._tile_coordinate_signature:
            index_groups: dict[tuple[int, int], list[int]] = {}
            for index, (x, y) in enumerate(coordinate_signature):
                index_groups.setdefault((x // self.chunk_size, y // self.chunk_size), []).append(index)
            self._tile_indices_by_chunk = {key: tuple(indices) for key, indices in index_groups.items()}
            self._tile_coordinate_signature = coordinate_signature
            self._tile_group_signatures.clear()
            self._terrain_chunks.clear()
        tile_groups = {}
        for chunk_key, indices in self._tile_indices_by_chunk.items():
            tiles = tuple(snapshot.tiles[index] for index in indices)
            if self._tile_group_signatures.get(chunk_key) != tiles:
                cache_key = (chunk_key[0], chunk_key[1], cell, self.quality,
                             self.show_exploration, self.show_grid)
                self._terrain_chunks.pop(cache_key, None)
                self._tile_group_signatures[chunk_key] = tiles
            tile_groups[chunk_key] = tiles
        for (chunk_x, chunk_y), tiles in tile_groups.items():
            tile_x, tile_y = chunk_x * self.chunk_size, chunk_y * self.chunk_size
            sx, sy = self.camera.world_to_screen((tile_x, tile_y))
            chunk_width = min(self.chunk_size, snapshot.width - tile_x) * cell
            chunk_height = min(self.chunk_size, snapshot.height - tile_y) * cell
            if sx + chunk_width <= 0 or sy + chunk_height <= 0 or sx >= logical_w or sy >= logical_h:
                continue
            chunk = self._terrain_chunk(tiles, chunk_x, chunk_y, cell)
            self.screen.blit(chunk, (origin_x + sx, origin_y + sy))
            visible_tiles += len(tiles)

        # Every building comes from the unique entity registry, so a multi-tile
        # footprint is rendered once using its authoritative dimensions.
        for building in snapshot.buildings:
            x, y = building["position"]
            sx, sy = self.camera.world_to_screen((x, y))
            fw, fh = building.get("footprint", (1, 1))
            width, height = max(8, round(cell * fw)), max(8, round(cell * fh))
            if sx + width <= 0 or sy + height <= 0 or sx >= logical_w or sy >= logical_h:
                continue
            integrity = building.get("integrity", 100)
            damaged = integrity is not None and integrity < 60
            online = bool(building.get("enabled", True)) and integrity != 0
            if building.get("powered") is False:
                online = False
            state = str(building.get("state", "")).lower()
            if not building.get("constructed", True):
                status = "construction"
            elif state == "abandoned":
                status = "abandoned"
            elif building.get("requires_maintenance") or "maintenance" in state:
                status = "maintenance"
            elif building.get("fully_operational") is False and online:
                status = "shortage"
            else:
                status = "operational"
            sprite = self._building_image(building.get("category", building.get("name", "Habitat")),
                                          width, height, online, damaged, status)
            self.screen.blit(sprite, (origin_x + sx, origin_y + sy))
            visible_buildings += 1
            if self.selected == ("building", building["id"]):
                pygame.draw.rect(self.screen, PALETTE["amber"],
                                 (origin_x + sx - 1, origin_y + sy - 1, width + 2, height + 2), 2)

        for agent in snapshot.agents:
            x, y = agent["position"]
            sx, sy = self.camera.world_to_screen((x, y))
            if sx + cell <= 0 or sy + cell <= 0 or sx >= logical_w or sy >= logical_h:
                continue
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
            appearance = dict(agent.get("appearance", {}))
            cargo = agent.get("cargo", {})
            appearance["carrying_load"] = bool(cargo and (not isinstance(cargo, dict) or
                                                          any(float(value) > 0 for value in cargo.values())))
            character = self._person_image(robot, frame, direction, activity,
                                           appearance, (width, height))
            px = sx + (cell - width) // 2
            py = sy + cell - height
            self.screen.blit(character, (origin_x + px, origin_y + py))
            visible_agents += 1
            if self.selected == ("agent", agent["id"]):
                pygame.draw.rect(self.screen, PALETTE["amber"],
                                 (origin_x + sx + 1, origin_y + sy + 1, cell - 2, cell - 2), 2)

        self._draw_dust(self.screen, viewport, now)
        self._draw_conversation_bubbles(snapshot, viewport, cell, now)
        if self.show_minimap:
            self._draw_minimap(snapshot, viewport)
        self.screen.set_clip(None)
        self.last_draw_stats = {"tiles": visible_tiles, "buildings": visible_buildings,
                                "agents": visible_agents, "temporary_world_surfaces": 0}
        self.last_frame_time_ms = (perf_counter() - frame_started) * 1000.0

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
            anchor = (viewport.x + sx,
                      viewport.y + sy - round(cell * 1.15))
            if not viewport.collidepoint(anchor):
                continue
            text = str(turn.get("text", ""))
            max_width = min(round(230 * self.ui_scale), viewport.width - 12)
            while text and self.bubble_font.size(text)[0] > max_width - round(14 * self.ui_scale):
                text = text[:-2] + "…" if len(text) > 2 else text[:-1]
            text_surface = self.bubble_font.render(text, False, (45, 37, 36))
            bubble_width = min(max_width, text_surface.get_width() + round(14 * self.ui_scale))
            bubble_height = round(25 * self.ui_scale)
            bx = max(viewport.left + 5, min(viewport.right - bubble_width - 5, anchor[0] - bubble_width // 2))
            by = max(viewport.top + 5, anchor[1] - bubble_height - round(6 * self.ui_scale))
            color = tuple(agent.get("appearance", {}).get("trim_color", PALETTE["cream"]))
            pygame.draw.rect(self.screen, (38, 30, 31),
                             (bx - 2, by - 2, bubble_width + 4, bubble_height + 4))
            pygame.draw.rect(self.screen, (235, 219, 181), (bx, by, bubble_width, bubble_height))
            pygame.draw.rect(self.screen, color, (bx, by, bubble_width, max(2, round(3 * self.ui_scale))))
            pygame.draw.polygon(self.screen, (235, 219, 181),
                                [(anchor[0] - 4, by + bubble_height),
                                 (anchor[0] + 4, by + bubble_height),
                                 (anchor[0], by + bubble_height + round(5 * self.ui_scale))])
            self.screen.blit(text_surface, (bx + round(7 * self.ui_scale), by + round(6 * self.ui_scale)))

    def _draw_dust(self, target: pygame.Surface, viewport: pygame.Rect, now: float) -> None:
        # Native-resolution fine streaks and flecks are presentation-only.
        for i in range(self.quality_options["dust"]):
            x = viewport.x + int((i * 97 + now * (3 + i % 3) * 7) % max(1, viewport.width))
            y = viewport.y + int((i * 53 + math.sin(now * .35 + i) * 9) % max(1, viewport.height))
            pygame.draw.circle(target, (185, 117, 84), (x, y), 1 + (i % 5 == 0))
            if i % 3 == 0:
                pygame.draw.line(target, (153, 94, 73), (x - 2, y + 1), (x + 3, y + 1), 1)

    def _draw_minimap(self, snapshot, viewport: pygame.Rect) -> None:
        width, height = round(132 * self.ui_scale), round(92 * self.ui_scale)
        x, y = viewport.left + round(12 * self.ui_scale), viewport.bottom - height - round(12 * self.ui_scale)
        if x + width > viewport.right - 8 or y < viewport.top + round(60 * self.ui_scale):
            return
        key = (snapshot.tick, snapshot.width, snapshot.height, width, height)
        if key != self._minimap_cache_key or self._minimap_surface is None:
            minimap = pygame.Surface((width, height))
            minimap.fill((33, 28, 31))
            map_rect = pygame.Rect(round(4 * self.ui_scale), round(4 * self.ui_scale),
                                   width - round(8 * self.ui_scale), height - round(8 * self.ui_scale))
            for tx, ty, terrain, explored, _occupied, _deposits, _region in snapshot.tiles:
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
            pygame.draw.rect(minimap, PALETTE["cream"], map_rect, max(1, round(self.ui_scale)))
            pygame.draw.rect(minimap, PALETTE["amber"], (0, 0, width, height), max(1, round(2 * self.ui_scale)))
            self._minimap_surface = minimap
            self._minimap_cache_key = key
            self.minimap_rebuild_count += 1
        x, y = int(x), int(y)
        self.screen.blit(self._minimap_surface, (x, y))

    def minimap_rect(self, viewport: pygame.Rect) -> pygame.Rect | None:
        width, height = round(132 * self.ui_scale), round(92 * self.ui_scale)
        margin = round(12 * self.ui_scale)
        rect = pygame.Rect(viewport.left + margin, viewport.bottom - height - margin, width, height)
        if (not self.show_minimap or rect.right > viewport.right - 8
                or rect.top < viewport.top + round(60 * self.ui_scale)):
            return None
        return rect

    def center_from_minimap(self, snapshot, point: tuple[int, int], viewport: pygame.Rect) -> bool:
        rect = self.minimap_rect(viewport)
        if rect is None or not rect.collidepoint(point):
            return False
        inset = round(4 * self.ui_scale)
        map_rect = pygame.Rect(rect.x + inset, rect.y + inset,
                               rect.width - 2 * inset, rect.height - 2 * inset)
        wx = (point[0] - map_rect.x) * snapshot.width / map_rect.width
        wy = (point[1] - map_rect.y) * snapshot.height / map_rect.height
        self.camera.center_on((wx, wy), viewport.size)
        return True

    def pick(self, snapshot, screen_position: tuple[int, int], viewport: pygame.Rect):
        """Resolve the actual world cell under the pointer at every zoom level."""
        if not viewport.collidepoint(screen_position):
            return None
        rect = self.minimap_rect(viewport)
        if rect and rect.collidepoint(screen_position):
            return "minimap", {"position": screen_position}
        local = (screen_position[0] - viewport.x, screen_position[1] - viewport.y)
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
                             "deposits": dict(tile[5]), "region": tile[6]}
        return None
