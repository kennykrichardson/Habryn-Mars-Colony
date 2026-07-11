"""
renderer.py

Habryn Visualization Renderer

PART 1 OF 3

Responsible for drawing the simulation world.

Responsibilities
----------------
- Camera
- Coordinate conversion
- Rendering initialization
- Terrain rendering
- Viewport
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import pygame

from colony.model import ColonyModel

# ============================================================
# Colors
# ============================================================


BLACK = (18, 18, 18)

WHITE = (245, 245, 245)

MARS = (168, 77, 48)

GRID = (75, 75, 75)

SELECT = (0, 255, 255)

TEXT = (230, 230, 230)

WARNING = (255, 165, 0)

DANGER = (255, 60, 60)

SUCCESS = (0, 200, 100)


# ============================================================
# Camera
# ============================================================


@dataclass
class Camera:

    x: float = 0

    y: float = 0

    zoom: float = 1.0

    speed: float = 12

    min_zoom: float = 0.35

    max_zoom: float = 3.5

    # --------------------------------------------------------

    def move(
        self,
        dx: float,
        dy: float,
    ) -> None:

        self.x += dx * self.speed

        self.y += dy * self.speed

    # --------------------------------------------------------

    def zoom_in(
        self,
        amount: float = 0.1,
    ) -> None:

        self.zoom = min(
            self.max_zoom,
            self.zoom + amount,
        )

    # --------------------------------------------------------

    def zoom_out(
        self,
        amount: float = 0.1,
    ) -> None:

        self.zoom = max(
            self.min_zoom,
            self.zoom - amount,
        )


# ============================================================
# Renderer
# ============================================================


class Renderer:

    def __init__(
        self,
        model: ColonyModel,
        width: int = 1400,
        height: int = 900,
        tile_size: int = 32,
    ) -> None:

        pygame.init()

        self.model = model

        self.width = width

        self.height = height

        self.tile_size = tile_size

        self.camera = Camera()

        self.selected = None

        self.screen = pygame.display.set_mode(
            (
                width,
                height,
            )
        )

        pygame.display.set_caption("Habryn")

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(
            "Consolas",
            16,
        )

    # ========================================================
    # Coordinate Conversion
    # ========================================================

    def world_to_screen(
        self,
        x: int,
        y: int,
    ) -> Tuple[int, int]:

        sx = ((x * self.tile_size) - self.camera.x) * self.camera.zoom

        sy = ((y * self.tile_size) - self.camera.y) * self.camera.zoom

        return (
            int(sx),
            int(sy),
        )

    # --------------------------------------------------------

    def screen_to_world(
        self,
        x: int,
        y: int,
    ) -> Tuple[int, int]:

        wx = (x / self.camera.zoom + self.camera.x) / self.tile_size

        wy = (y / self.camera.zoom + self.camera.y) / self.tile_size

        return (
            int(wx),
            int(wy),
        )

    # ========================================================
    # Frame
    # ========================================================

    def begin_frame(
        self,
    ) -> None:

        self.screen.fill(BLACK)

    # ========================================================
    # Terrain
    # ========================================================

    def render_terrain(
        self,
    ) -> None:

        mars = self.model.mars_map

        for y in range(mars.height):

            for x in range(mars.width):

                tile = mars.get_tile(
                    x,
                    y,
                )

                sx, sy = self.world_to_screen(
                    x,
                    y,
                )

                size = int(self.tile_size * self.camera.zoom)

                pygame.draw.rect(
                    self.screen,
                    MARS,
                    (
                        sx,
                        sy,
                        size,
                        size,
                    ),
                )

                pygame.draw.rect(
                    self.screen,
                    GRID,
                    (
                        sx,
                        sy,
                        size,
                        size,
                    ),
                    1,
                )

    # ========================================================
    # Grid
    # ========================================================

    def render_grid(
        self,
    ) -> None:

        mars = self.model.mars_map

        size = int(self.tile_size * self.camera.zoom)

        for x in range(mars.width + 1):

            sx = x * size - self.camera.x

            pygame.draw.line(
                self.screen,
                GRID,
                (
                    sx,
                    0,
                ),
                (
                    sx,
                    self.height,
                ),
            )

        for y in range(mars.height + 1):

            sy = y * size - self.camera.y

            pygame.draw.line(
                self.screen,
                GRID,
                (
                    0,
                    sy,
                ),
                (
                    self.width,
                    sy,
                ),
            )

        # ========================================================

    # Buildings
    # ========================================================

    def render_buildings(
        self,
    ) -> None:

        size = int(self.tile_size * self.camera.zoom)

        for building in self.model.buildings:

            sx, sy = self.world_to_screen(
                building.position[0],
                building.position[1],
            )

            color = (120, 180, 255)

            if not building.powered:

                color = WARNING

            if building.integrity < 35:

                color = DANGER

            pygame.draw.rect(
                self.screen,
                color,
                (
                    sx + 3,
                    sy + 3,
                    size - 6,
                    size - 6,
                ),
            )

            if building == self.selected:

                pygame.draw.rect(
                    self.screen,
                    SELECT,
                    (
                        sx + 1,
                        sy + 1,
                        size - 2,
                        size - 2,
                    ),
                    2,
                )

    # ========================================================
    # Astronauts
    # ========================================================

    def render_astronauts(
        self,
    ) -> None:

        radius = max(
            4,
            int(5 * self.camera.zoom),
        )

        for astronaut in self.model.astronauts:

            sx, sy = self.world_to_screen(
                astronaut.position[0],
                astronaut.position[1],
            )

            pygame.draw.circle(
                self.screen,
                WHITE,
                (
                    sx + self.tile_size // 2,
                    sy + self.tile_size // 2,
                ),
                radius,
            )

            if astronaut == self.selected:

                pygame.draw.circle(
                    self.screen,
                    SELECT,
                    (
                        sx + self.tile_size // 2,
                        sy + self.tile_size // 2,
                    ),
                    radius + 3,
                    2,
                )

    # ========================================================
    # Robots
    # ========================================================

    def render_robots(
        self,
    ) -> None:

        radius = max(
            4,
            int(5 * self.camera.zoom),
        )

        for robot in self.model.robots:

            sx, sy = self.world_to_screen(
                robot.position[0],
                robot.position[1],
            )

            pygame.draw.circle(
                self.screen,
                SUCCESS,
                (
                    sx + self.tile_size // 2,
                    sy + self.tile_size // 2,
                ),
                radius,
            )

            if robot == self.selected:

                pygame.draw.circle(
                    self.screen,
                    SELECT,
                    (
                        sx + self.tile_size // 2,
                        sy + self.tile_size // 2,
                    ),
                    radius + 3,
                    2,
                )

    # ========================================================
    # Selection
    # ========================================================

    def render_selection(
        self,
    ) -> None:

        if self.selected is None:

            return

        lines = [
            f"Selected : {type(self.selected).__name__}",
        ]

        if hasattr(
            self.selected,
            "name",
        ):

            lines.append(f"Name : {self.selected.name}")

        if hasattr(
            self.selected,
            "health",
        ):

            lines.append(f"Health : {self.selected.health:.1f}")

        if hasattr(
            self.selected,
            "integrity",
        ):

            lines.append(f"Integrity : {self.selected.integrity:.1f}")

        if hasattr(
            self.selected,
            "status",
        ):

            status = self.selected.status

            if hasattr(
                status,
                "value",
            ):

                status = status.value

            lines.append(f"Status : {status}")

        y = 20

        for line in lines:

            surface = self.font.render(
                line,
                True,
                TEXT,
            )

            self.screen.blit(
                surface,
                (
                    20,
                    y,
                ),
            )

            y += 22

    # ========================================================
    # Weather Overlay
    # ========================================================

    def render_weather(
        self,
    ) -> None:

        weather = getattr(
            self.model,
            "weather",
            None,
        )

        if weather is None:

            return

        if hasattr(
            weather,
            "storm_active",
        ):

            if weather.storm_active:

                overlay = pygame.Surface(
                    (
                        self.width,
                        self.height,
                    ),
                    pygame.SRCALPHA,
                )

                overlay.fill(
                    (
                        170,
                        120,
                        70,
                        80,
                    )
                )

                self.screen.blit(
                    overlay,
                    (
                        0,
                        0,
                    ),
                )

        # ========================================================

    # Statistics Overlay
    # ========================================================

    def render_statistics(
        self,
    ) -> None:

        statistics = self.model.statistics()

        x = self.width - 260

        y = 20

        title = self.font.render(
            "COLONY STATUS",
            True,
            WHITE,
        )

        self.screen.blit(
            title,
            (
                x,
                y,
            ),
        )

        y += 28

        for key, value in statistics.items():

            text = self.font.render(
                f"{key}: {value}",
                True,
                TEXT,
            )

            self.screen.blit(
                text,
                (
                    x,
                    y,
                ),
            )

            y += 20

    # ========================================================
    # FPS
    # ========================================================

    def render_fps(
        self,
    ) -> None:

        fps = int(self.clock.get_fps())

        color = SUCCESS

        if fps < 30:

            color = WARNING

        if fps < 15:

            color = DANGER

        surface = self.font.render(
            f"FPS: {fps}",
            True,
            color,
        )

        self.screen.blit(
            surface,
            (
                15,
                self.height - 35,
            ),
        )

    # ========================================================
    # Event Processing
    # ========================================================

    def process_events(
        self,
    ) -> bool:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                return False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    return False

                elif event.key == pygame.K_UP:

                    self.camera.move(
                        0,
                        -1,
                    )

                elif event.key == pygame.K_DOWN:

                    self.camera.move(
                        0,
                        1,
                    )

                elif event.key == pygame.K_LEFT:

                    self.camera.move(
                        -1,
                        0,
                    )

                elif event.key == pygame.K_RIGHT:

                    self.camera.move(
                        1,
                        0,
                    )

                elif event.key in (
                    pygame.K_EQUALS,
                    pygame.K_PLUS,
                ):

                    self.camera.zoom_in()

                elif event.key == pygame.K_MINUS:

                    self.camera.zoom_out()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    wx, wy = self.screen_to_world(*event.pos)

                    self.selected = None

                    for building in self.model.buildings:

                        if building.position == (
                            wx,
                            wy,
                        ):

                            self.selected = building

                            break

                    if self.selected is None:

                        for astronaut in self.model.astronauts:

                            if astronaut.position == (
                                wx,
                                wy,
                            ):

                                self.selected = astronaut

                                break

                    if self.selected is None:

                        for robot in self.model.robots:

                            if robot.position == (
                                wx,
                                wy,
                            ):

                                self.selected = robot

                                break

                elif event.button == 4:

                    self.camera.zoom_in()

                elif event.button == 5:

                    self.camera.zoom_out()

        return True

    # ========================================================
    # Render
    # ========================================================

    def render(
        self,
    ) -> None:

        self.begin_frame()

        self.render_terrain()

        self.render_grid()

        self.render_buildings()

        self.render_astronauts()

        self.render_robots()

        self.render_weather()

        self.render_selection()

        self.render_statistics()

        self.render_fps()

        pygame.display.flip()

        self.clock.tick(60)

    # ========================================================
    # Main Loop
    # ========================================================

    def run(
        self,
    ) -> None:

        running = True

        while running:

            running = self.process_events()

            self.model.step()

            self.render()

        pygame.quit()

    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Renderer(" f"{self.width}x{self.height}, " f"Zoom={self.camera.zoom:.2f})"
        )
