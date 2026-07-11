"""
dashboard.py

Habryn Colony Dashboard

Displays the live status of the colony while the renderer
draws the simulation world.

Responsibilities
----------------
- Colony Overview
- Resource Panels
- Population Summary
- Building Statistics
- Alerts
- Simulation Speed
- Current Time
- FPS
"""

from __future__ import annotations
from colony.visualization.renderer import Renderer
from dataclasses import dataclass
from typing import Dict

import pygame

# ============================================================
# Colors
# ============================================================

BACKGROUND = (30, 30, 36)

PANEL = (40, 40, 48)

TEXT = (235, 235, 235)

SUCCESS = (40, 210, 90)

WARNING = (240, 180, 20)

DANGER = (235, 70, 70)

BLUE = (70, 160, 255)

CYAN = (0, 210, 255)


# ============================================================
# Dashboard
# ============================================================


@dataclass
class Dashboard:

    renderer: Renderer

    width: int = 320

    padding: int = 15

    # ========================================================

    def __post_init__(self):

        self.font = pygame.font.SysFont(
            "Consolas",
            16,
        )

        self.title_font = pygame.font.SysFont(
            "Consolas",
            20,
            bold=True,
        )

    # ========================================================

    def draw_panel(
        self,
        surface,
        x,
        y,
        width,
        height,
    ):

        pygame.draw.rect(
            surface,
            PANEL,
            (
                x,
                y,
                width,
                height,
            ),
            border_radius=8,
        )

    # ========================================================

    def draw_text(
        self,
        surface,
        text,
        x,
        y,
        color=TEXT,
    ):

        label = self.font.render(
            str(text),
            True,
            color,
        )

        surface.blit(
            label,
            (
                x,
                y,
            ),
        )

    # ========================================================

    def draw_title(
        self,
        surface,
        text,
        x,
        y,
    ):

        label = self.title_font.render(
            text,
            True,
            CYAN,
        )

        surface.blit(
            label,
            (
                x,
                y,
            ),
        )

    # ========================================================
    # Colony
    # ========================================================

    def draw_colony_summary(
        self,
        surface,
        x,
        y,
    ):

        model = self.renderer.model

        self.draw_title(
            surface,
            "COLONY",
            x,
            y,
        )

        y += 35

        self.draw_text(
            surface,
            f"Astronauts : {len(model.astronauts)}",
            x,
            y,
        )

        y += 22

        self.draw_text(
            surface,
            f"Robots : {len(model.robots)}",
            x,
            y,
        )

        y += 22

        self.draw_text(
            surface,
            f"Buildings : {len(model.buildings)}",
            x,
            y,
        )

        y += 22

        self.draw_text(
            surface,
            f"Hour : {model.current_hour}",
            x,
            y,
            BLUE,
        )

    # ========================================================
    # Resources
    # ========================================================

    def draw_resources(
        self,
        surface,
        x,
        y,
    ):

        model = self.renderer.model

        self.draw_title(
            surface,
            "RESOURCES",
            x,
            y,
        )

        y += 35

        resources = [
            ("Oxygen", model.oxygen),
            ("Water", model.water),
            ("Food", model.food),
            ("Power", model.power),
            ("Minerals", model.minerals),
        ]

        for name, resource in resources:

            percentage = round(
                resource.fill_percentage,
                1,
            )

            color = SUCCESS

            if percentage < 50:

                color = WARNING

            if percentage < 20:

                color = DANGER

            self.draw_text(
                surface,
                f"{name:<10} {percentage:>6}%",
                x,
                y,
                color,
            )

            y += 22

    # ========================================================
    # Alerts
    # ========================================================

    def draw_alerts(
        self,
        surface,
        x,
        y,
    ):

        ai = self.renderer.model.ai_manager

        self.draw_title(
            surface,
            "ALERT",
            x,
            y,
        )

        y += 35

        alert = ai.alert_level.value

        color = SUCCESS

        if alert == "Yellow":

            color = WARNING

        elif alert in (
            "Orange",
            "Red",
            "Critical",
        ):

            color = DANGER

        self.draw_text(
            surface,
            alert,
            x,
            y,
            color,
        )

    # ========================================================
    # Performance
    # ========================================================

    def draw_performance(
        self,
        surface,
        x,
        y,
    ):

        fps = int(self.renderer.clock.get_fps())

        self.draw_title(
            surface,
            "PERFORMANCE",
            x,
            y,
        )

        y += 35

        self.draw_text(
            surface,
            f"FPS : {fps}",
            x,
            y,
        )

        y += 22

        self.draw_text(
            surface,
            "Simulation : Running",
            x,
            y,
        )

    # ========================================================
    # Draw
    # ========================================================

    def draw(
        self,
        surface,
    ):

        panel_x = self.renderer.width - self.width

        pygame.draw.rect(
            surface,
            BACKGROUND,
            (
                panel_x,
                0,
                self.width,
                self.renderer.height,
            ),
        )

        self.draw_colony_summary(
            surface,
            panel_x + self.padding,
            20,
        )

        self.draw_resources(
            surface,
            panel_x + self.padding,
            180,
        )

        self.draw_alerts(
            surface,
            panel_x + self.padding,
            360,
        )

        self.draw_performance(
            surface,
            panel_x + self.padding,
            470,
        )

    # ========================================================

    def statistics(
        self,
    ) -> Dict:

        model = self.renderer.model

        return {
            "population": len(model.astronauts),
            "robots": len(model.robots),
            "buildings": len(model.buildings),
        }
