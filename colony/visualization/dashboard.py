"""Small telemetry panel for callers that compose their own Pygame layout."""
from __future__ import annotations

from dataclasses import dataclass
import pygame

from colony.visualization.renderer import Renderer


@dataclass
class Dashboard:
    renderer: Renderer
    width: int = 300
    padding: int = 16

    def __post_init__(self):
        self.font = pygame.font.SysFont("segoe ui", 15)
        self.title_font = pygame.font.SysFont("segoe ui", 19, bold=True)

    def draw(self, surface: pygame.Surface, snapshot=None):
        snapshot = snapshot or getattr(self.renderer, "last_snapshot", None)
        if snapshot is None:
            return
        x = surface.get_width() - self.width
        pygame.draw.rect(surface, (35, 36, 38), (x, 0, self.width, surface.get_height()))
        y = self.padding
        def line(text, color=(230, 224, 215), font=None):
            nonlocal y
            surface.blit((font or self.font).render(str(text), True, color), (x + self.padding, y))
            y += 25
        line("COLONY TELEMETRY", (224, 161, 93), self.title_font)
        line(snapshot.time)
        line(f"Tick  {snapshot.tick:,}")
        line(f"Population  {len(snapshot.agents)}")
        line(f"Buildings  {len(snapshot.buildings)}")
        line(f"World  {snapshot.width} × {snapshot.height}")

    def statistics(self, snapshot=None):
        snapshot = snapshot or getattr(self.renderer, "last_snapshot", None)
        if snapshot is None:
            return {"population": 0, "buildings": 0}
        return {"population": len(snapshot.agents), "robots": sum(a["category"] == "robot" for a in snapshot.agents),
                "buildings": len(snapshot.buildings)}
