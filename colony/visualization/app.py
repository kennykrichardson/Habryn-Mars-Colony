"""Retro pixel-art Mission Control interface for Habryn."""
from __future__ import annotations

import ctypes
import sys
from collections import OrderedDict

import pygame

from colony.simulation import Simulation
from colony.initialization import ColonyConfig
from colony.visualization.pixel_art import character_sprite
from colony.visualization.renderer import Camera, Renderer
from colony.systems.research_manager import RESEARCH_TECH_TREE
from colony.visualization.render_settings import DISPLAY_PRESETS, QUALITY_PRESETS, DisplaySettings

BG = (24, 20, 24)
PANEL = (39, 29, 33)
PANEL_DARK = (31, 25, 29)
TEXT = (235, 216, 179)
MUTED = (166, 141, 121)
ACCENT = (224, 154, 88)
CYAN = (106, 205, 213)
GREEN = (129, 178, 123)
AMBER = (229, 166, 78)
RED = (211, 91, 72)
HEADER_HEIGHT = 62
SIDEBAR_WIDTH = 320
RESEARCH_PROJECTS = {
    "Solar Efficiency": ("Improve solar array conversion and power yield.", 160, "+15% solar output"),
    "Crop Yield": ("Improve greenhouse growth and harvest yield.", 140, "+20% crop growth"),
    "Oxygen Recovery": ("Tune life-support oxygen generation.", 180, "+15% oxygen output"),
    "Water Recovery": ("Reduce loss in the water treatment loop.", 180, "+15% water output"),
    "Robotics": ("Improve robot firmware and work efficiency.", 220, "+10% robot efficiency"),
    "Medical Care": ("Improve clinical protocols and recovery.", 160, "+10% medical efficiency"),
}


class HabrynApp:
    def __init__(self, simulation: Simulation | None = None, size=(1280, 800), *,
                 quality: str = "High", ui_scale: float | None = None, fullscreen: bool = False):
        self._enable_per_monitor_dpi_awareness()
        pygame.init()
        pygame.display.set_caption("HABRYN // MARS COLONY MISSION CONTROL")
        if isinstance(size, str):
            if size.lower() == "native":
                size = self._desktop_size()
            else:
                try:
                    size = DISPLAY_PRESETS[size.lower()]
                except KeyError as error:
                    raise ValueError(f"Unknown display size preset: {size}") from error
        elif size is None:
            size = self._desktop_size()
        self.display_settings = DisplaySettings(width=size[0], height=size[1], fullscreen=fullscreen,
                                                quality=quality, ui_scale=ui_scale)
        self.windowed_size = tuple(size)
        if fullscreen:
            try:
                self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
            except pygame.error:
                desktop_size = self._desktop_size()
                self.screen = pygame.display.set_mode(desktop_size, pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.fullscreen = fullscreen
        self._ui_scale_explicit = ui_scale is not None
        self.ui_scale = ui_scale if ui_scale is not None else self._display_dpi_scale(size)
        self._apply_ui_scale()
        if hasattr(pygame.display, "set_minimum_size"):
            pygame.display.set_minimum_size((self.u(960), self.u(640)))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 12, bold=True)
        self.title_font = pygame.font.SysFont("monospace", 20, bold=True)
        self._text_surfaces: OrderedDict[tuple, pygame.Surface] = OrderedDict()
        self.text_cache_hits = 0
        self.text_cache_misses = 0
        self.simulation = simulation or Simulation()
        self.simulation.start()
        self.camera = Camera()
        self.camera_centered = False
        self.renderer = Renderer(self.screen, self.camera, self.simulation.config.seed,
                                 quality=quality, ui_scale=self.ui_scale)
        self.paused = False
        self.accumulator = 0.0
        self.drag: tuple[int, int] | None = None
        self.selected: tuple[str, object] | None = None
        self.panel_scroll = 0
        self.panel_content_height = 0
        self.research_scroll = 0
        self.running = True
        self.speed_levels = (.25, .5, 1.0, 2.0, 4.0, 8.0)
        self.speed_index = 2
        self.crew_mode = False
        self.crew_filter = "all"
        self.crew_sort = "name"
        self.crew_scroll = 0
        self.crew_rows: list[tuple[pygame.Rect, object]] = []
        self.buttons: dict[str, pygame.Rect] = {}
        self.last_viewport = pygame.Rect(0, self.u(HEADER_HEIGHT), 1, 1)
        self.last_snapshot = None
        self._last_paused_frame_key = None
        self.paused_redraw_skips = 0
        self.scenario_mode = False
        self.research_mode = False
        self.research_message = ""
        self.build_mode = False
        self.selected_building_type = "SolarArray"
        self.build_message = ""
        self.build_palette = {}

    @staticmethod
    def _desktop_size() -> tuple[int, int]:
        sizes = pygame.display.get_desktop_sizes()
        if sizes:
            return sizes[0]
        info = pygame.display.Info()
        return max(640, info.current_w), max(480, info.current_h)

    @staticmethod
    def _dpi_scale(size: tuple[int, int]) -> float:
        """Portable fallback used when the display backend exposes no physical DPI."""
        return min(2.0, max(1.0, round(max(size[0] / 1600, size[1] / 900) * 4) / 4))

    @staticmethod
    def _enable_per_monitor_dpi_awareness() -> None:
        """Ask Windows for monitor-aware window coordinates before SDL creates a window."""
        if sys.platform != "win32":
            return
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except (AttributeError, OSError):
                pass

    def _display_dpi_scale(self, size: tuple[int, int]) -> float:
        """Prefer the current window's monitor DPI, then use a size-based fallback."""
        if sys.platform == "win32":
            try:
                handle = pygame.display.get_wm_info().get("window")
                if handle:
                    dpi = ctypes.windll.user32.GetDpiForWindow(ctypes.c_void_p(handle))
                    if dpi:
                        return max(.75, min(3.0, dpi / 96.0))
            except (AttributeError, OSError, TypeError, ValueError):
                pass
        return self._dpi_scale(size)

    def u(self, value: float) -> int:
        return max(1, round(value * self.ui_scale))

    def _apply_ui_scale(self) -> None:
        self.ui_scale = max(.75, min(3.0, float(self.ui_scale)))
        self.font = pygame.font.SysFont("monospace", self.u(14), bold=True)
        self.small_font = pygame.font.SysFont("monospace", self.u(12), bold=True)
        self.title_font = pygame.font.SysFont("monospace", self.u(20), bold=True)
        if hasattr(self, "_text_surfaces"):
            self._text_surfaces.clear()
        if hasattr(self, "renderer"):
            self.renderer.set_ui_scale(self.ui_scale)
        if hasattr(self, "screen") and hasattr(pygame.display, "set_minimum_size"):
            pygame.display.set_minimum_size((self.u(960), self.u(640)))

    def set_quality(self, quality: str) -> None:
        self.renderer.set_quality(quality)
        self.display_settings = DisplaySettings(width=self.screen.get_width(), height=self.screen.get_height(),
            fullscreen=self.fullscreen, quality=quality,
            ui_scale=self.ui_scale if self._ui_scale_explicit else None)

    def set_ui_scale(self, scale: float) -> None:
        if not .75 <= scale <= 3.0:
            raise ValueError("UI scale must be between 0.75 and 3.0")
        self._ui_scale_explicit = True
        self.ui_scale = float(scale)
        self._apply_ui_scale()
        self.display_settings = DisplaySettings(width=self.screen.get_width(), height=self.screen.get_height(),
            fullscreen=self.fullscreen, quality=self.renderer.quality, ui_scale=self.ui_scale)

    def toggle_fullscreen(self) -> None:
        current_center = self._camera_center()
        if self.fullscreen:
            self.fullscreen = False
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        else:
            self.windowed_size = self.screen.get_size()
            self.fullscreen = True
            desktop_size = self._desktop_size()
            try:
                self.screen = pygame.display.set_mode(desktop_size, pygame.FULLSCREEN)
            except pygame.error:
                self.screen = pygame.display.set_mode(desktop_size, pygame.NOFRAME)
        self.renderer.screen = self.screen
        if not self._ui_scale_explicit:
            self.ui_scale = self._display_dpi_scale(self.screen.get_size())
            self._apply_ui_scale()
        _width, _height, _side, viewport, _panel = self._layout()
        self.camera.center_on(current_center, viewport.size)
        self.display_settings = DisplaySettings(width=self.screen.get_width(), height=self.screen.get_height(),
            fullscreen=self.fullscreen, quality=self.renderer.quality,
            ui_scale=self.ui_scale if self._ui_scale_explicit else None)

    def _camera_center(self) -> tuple[float, float]:
        cell = self.camera.cell
        return (self.camera.x + self.last_viewport.width / (2 * cell),
                self.camera.y + self.last_viewport.height / (2 * cell))

    def label(self, text, position, color=TEXT, font=None):
        font = font or self.font
        value = str(text)
        key = (id(font), value, color)
        image = self._text_surfaces.get(key)
        if image is None:
            image = font.render(value, False, color)
            self._text_surfaces[key] = image
            self.text_cache_misses += 1
            if len(self._text_surfaces) > 4096:
                self._text_surfaces.popitem(last=False)
        else:
            self._text_surfaces.move_to_end(key)
            self.text_cache_hits += 1
        self.screen.blit(image, position)

    @staticmethod
    def _wrap(text: str, font: pygame.font.Font, width: int) -> list[str]:
        """Wrap readable text on word boundaries for a bounded panel width."""
        words = str(text).split()
        if not words:
            return [""]
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and font.size(candidate)[0] > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def _wrapped_label(self, text: str, position: tuple[int, int], width: int,
                       color=TEXT, font=None, line_gap: int = 2) -> int:
        font = font or self.font
        line_height = font.get_linesize() + self.u(line_gap)
        for index, line in enumerate(self._wrap(text, font, width)):
            self.label(line, (position[0], position[1] + index * line_height), color, font)
        return max(1, len(self._wrap(text, font, width))) * line_height

    def _button(self, key: str, rect, text: str, active=False):
        rect = pygame.Rect(rect)
        self.buttons[key] = rect
        fill = (70, 48, 44) if active else (47, 37, 39)
        edge = ACCENT if active else (111, 80, 65)
        pygame.draw.rect(self.screen, fill, rect)
        pygame.draw.rect(self.screen, edge, rect, 2)
        title = self.font.render(text, False, TEXT)
        self.screen.blit(title, title.get_rect(center=rect.center))

    def _layout(self):
        width, height = self.screen.get_size()
        header_height = self.u(HEADER_HEIGHT)
        side_w = min(self.u(SIDEBAR_WIDTH), max(self.u(280), width // 3))
        panel = pygame.Rect(width - side_w, header_height, side_w, height - header_height)
        viewport = pygame.Rect(0, header_height, panel.x, height - header_height)
        self.last_viewport = viewport
        return width, height, side_w, viewport, panel

    def _draw_header(self, width: int, snapshot):
        header_height = self.u(HEADER_HEIGHT)
        pygame.draw.rect(self.screen, (42, 28, 33), (0, 0, width, header_height))
        pygame.draw.line(self.screen, ACCENT, (0, header_height - self.u(2)), (width, header_height - self.u(2)), self.u(2))
        self.label(self._fit(self.simulation.config.colony_name.upper(), self.u(160), self.title_font),
                   (self.u(18), self.u(10)), ACCENT, self.title_font)
        self.label(self._fit(f"MARS / {self.simulation.config.colony_id}", self.u(160), self.small_font),
                   (self.u(20), self.u(38)), MUTED, self.small_font)
        self.label(snapshot.time.upper(), (self.u(194), self.u(15)), CYAN)
        self.label(f"TICK {snapshot.tick:07d}", (self.u(194), self.u(37)), MUTED, self.small_font)
        self.buttons.clear()
        x = max(self.u(310), width - self.u(630))
        self._button("pause", (x, self.u(13), self.u(78), self.u(36)), "RESUME" if self.paused else "PAUSE", active=self.paused)
        self._button("slower", (x + self.u(86), self.u(13), self.u(34), self.u(36)), "−")
        self.label(f"{self.simulation.simulation_speed:g}X", (x + self.u(126), self.u(23)), TEXT, self.small_font)
        self._button("faster", (x + self.u(166), self.u(13), self.u(34), self.u(36)), "+")
        self._button("step", (x + self.u(208), self.u(13), self.u(60), self.u(36)), "STEP", active=self.paused)
        self._button("grid", (x + self.u(276), self.u(13), self.u(48), self.u(36)), "GRID", active=self.renderer.show_grid)
        self._button("map", (x + self.u(332), self.u(13), self.u(48), self.u(36)), "MAP", active=self.renderer.show_minimap)
        self._button("crew", (x + self.u(388), self.u(13), self.u(60), self.u(36)), "CREW", active=self.crew_mode)
        self._button("new", (x + self.u(454), self.u(13), self.u(60), self.u(36)), "NEW", active=self.scenario_mode)
        self._button("research", (x + self.u(520), self.u(13), self.u(60), self.u(36)), "R&D", active=self.research_mode)

    def _draw_meter(self, rect, percentage: float, color):
        pygame.draw.rect(self.screen, (25, 23, 26), rect)
        pygame.draw.rect(self.screen, (86, 66, 58), rect, self.u(1))
        amount = int((rect.width - 2) * max(0, min(100, percentage)) / 100)
        if amount:
            pygame.draw.rect(self.screen, color, (rect.x + 1, rect.y + 1, amount, rect.height - 2))

    def _draw_sidebar(self, panel: pygame.Rect, snapshot):
        pygame.draw.rect(self.screen, PANEL, panel)
        pygame.draw.line(self.screen, (116, 77, 62), panel.topleft, (panel.x, panel.bottom), 2)
        selected_height = min(self.u(196), max(self.u(168), panel.height // 3))
        selection_rect = pygame.Rect(panel.x + self.u(8), panel.y + self.u(8),
                                     panel.width - self.u(16), selected_height - self.u(12))
        self.selected_card_rect = selection_rect.copy()
        content_rect = pygame.Rect(panel.x, panel.y + selected_height,
                                   panel.width, max(0, panel.height - selected_height))
        self.screen.set_clip(content_rect)
        left = panel.x + self.u(16)
        right = panel.right - self.u(16)
        y = content_rect.y + self.u(10) - self.panel_scroll
        self.label("COLONY / STATUS", (left, y), ACCENT, self.font)
        y += self.u(27)
        telemetry = snapshot.telemetry
        population = telemetry.get("population", {})
        humans = sum(a.get("category") == "agent" for a in snapshot.agents)
        robots = sum(a.get("category") == "robot" for a in snapshot.agents)
        facts = [
            ("CREW", f"{humans:02d}"), ("ROBOTS", f"{robots:02d}"),
            ("HOUSING", f"{population.get('occupied_housing', 0)}/{population.get('housing_capacity', 0)}"),
            ("STRUCTURES", str(len(snapshot.buildings))),
            ("SURVEY", f"{telemetry.get('map', {}).get('explored_tiles', 0)}/{snapshot.width * snapshot.height}"),
        ]
        colw = (panel.width - self.u(40)) // 2
        for index, (name, value) in enumerate(facts):
            col = index % 2
            row = index // 2
            xx, yy = left + col * colw, y + row * self.u(34)
            self.label(name, (xx, yy), MUTED, self.small_font)
            self.label(value, (xx, yy + self.u(13)), TEXT)
        y += ((len(facts) + 1) // 2) * self.u(34) + self.u(10)

        warnings = telemetry.get("warnings", ())
        if warnings:
            self.label("! RESOURCE WARNING", (left, y), RED)
            y += self.u(19)
            warning_text = ", ".join(warnings)
            y += self._wrapped_label(warning_text, (left, y), right - left, RED, self.small_font)

        goals = telemetry.get("ai_goals", ())
        if goals:
            self._section(left, y, "AI PRIORITIES")
            y += self.u(21)
            for goal in sorted(goals, key=lambda item: (-item.get("priority", 0), item.get("title", ""))):
                blocked = goal.get("status") == "blocked"
                color = RED if blocked or goal.get("severity") == "critical" else AMBER
                y += self._wrapped_label(goal.get("title", "Colony goal"), (left, y),
                                         right - left, color, self.small_font)
                y += self._wrapped_label(goal.get("reason", ""), (left, y), right - left,
                                         MUTED, self.small_font)
        forecasts = telemetry.get("resource_forecasts", {})
        projected = [(name, state) for name, state in forecasts.items()
                     if state.get("hours_until_empty") is not None]
        if projected:
            name, state = min(projected, key=lambda item: item[1]["hours_until_empty"])
            self.label(self._fit(f"FORECAST: {name} ~{state['hours_until_empty']:.0f}h",
                                 right - left, self.small_font), (left, y), AMBER, self.small_font)
            y += self.u(19)

        self._section(left, y, "RESOURCE STORES")
        y += self.u(24)
        resources = telemetry.get("resource_inventory", {})
        for name, value in resources.items():
            amount, capacity = value["current_amount"], value["storage_capacity"]
            fill = value["fill_percentage"]
            color = RED if name in warnings or fill < 20 else CYAN if name in {"Power", "Oxygen", "Water"} else GREEN
            self.label(name.upper(), (left, y), TEXT, self.small_font)
            value_text = f"{amount:,.0f}/{capacity:,.0f} {value['unit']}"
            self.label(value_text, (right - self.font.size(value_text)[0], y), MUTED, self.small_font)
            y += self.u(17)
            self._draw_meter(pygame.Rect(left, y, right - left, self.u(6)), fill, color)
            y += self.u(13)
            if name == "Fuel":
                fuel = telemetry.get("fuel_logistics", {})
                details = (f"MAP {fuel.get('deposit_amount', 0):,.0f} L  ·  "
                           f"CARGO {fuel.get('in_transit', 0):,.0f} L  ·  "
                           f"TASKS {len(fuel.get('active_tasks', ()))}")
                y += self._wrapped_label(details, (left, y), right - left,
                                         AMBER if "Fuel" in warnings else MUTED, self.small_font)

        y += self.u(3)
        self._section(left, y, "INFRASTRUCTURE")
        y += self.u(24)
        for building in snapshot.buildings:
            kind = building.get("category", building.get("name", "Facility"))
            name = str(building.get("name", kind))
            integrity = building.get("integrity", 100)
            if building.get("powered") is False:
                status, color = "NO PWR", RED
            elif not building.get("enabled", True):
                status, color = "OFF", MUTED
            elif integrity is not None and integrity < 60:
                status, color = "DAMAGED", AMBER
            else:
                status, color = "ONLINE", GREEN
            name_width = right - left - self.u(65)
            self._wrapped_label(name, (left, y), name_width, TEXT, self.small_font)
            self.label(status, (right - self.small_font.size(status)[0], y), color, self.small_font)
            y += max(self.u(19), (len(self._wrap(name, self.small_font, name_width)) *
                                  (self.small_font.get_linesize() + self.u(2))))
            if building.get("category") == "Greenhouse":
                crop = f"CROPS {building.get('crop_stage', 'Unknown').upper()} · HEALTH {building.get('crop_health', 0):.0f}%"
                self.label(self._fit(crop, right - left, self.small_font),
                           (left, y), GREEN if building.get("crop_health", 0) >= 60 else AMBER,
                           self.small_font)
                y += self.u(14)

        y += self.u(4)
        self._section(left, y, "RECENT EVENTS")
        y += self.u(24)
        events = telemetry.get("events_feed", ())
        if events:
            for event in events:
                y += self._wrapped_label(event.get("name", "Colony event"), (left, y),
                                         right - left, AMBER, self.small_font)
                y += self._wrapped_label(event.get("description", ""), (left, y), right - left,
                                         MUTED, self.small_font)
        else:
            self.label("NO ACTIVE ALERTS", (left, y), MUTED, self.small_font)
            y += self.u(18)

        y += self.u(3)
        self._section(left, y, "CREW COMMS")
        y += self.u(22)
        conversations = telemetry.get("conversations", ())
        relevant = [item for item in conversations if not self.selected or self.selected[0] != "agent"
                    or self.selected[1].get("id") in item.get("participants", ())]
        recent = relevant
        if recent:
            for conversation in recent:
                for turn in conversation.get("turns", ()):
                    line = f"{turn.get('speaker', 'Crew')}: {turn.get('text', '')}"
                    y += self._wrapped_label(line, (left, y), right - left, CYAN, self.small_font)
        else:
            self.label("NO RECENT CONVERSATIONS", (left, y), MUTED, self.small_font)
            y += self.u(17)

        self.panel_content_height = y + self.panel_scroll - content_rect.y
        max_scroll = max(0, self.panel_content_height - content_rect.height + self.u(12))
        self.panel_scroll = min(self.panel_scroll, max_scroll)
        self.screen.set_clip(selection_rect)
        self._draw_selected_card(selection_rect)
        self.screen.set_clip(panel)
        self.screen.set_clip(None)
        if max_scroll:
            track = pygame.Rect(panel.right - self.u(7), content_rect.y + self.u(8),
                                self.u(3), max(1, content_rect.height - self.u(16)))
            thumb_height = max(self.u(24), round(track.height * content_rect.height /
                                                 max(1, self.panel_content_height)))
            thumb_y = track.y + round((track.height - thumb_height) * self.panel_scroll / max_scroll)
            pygame.draw.rect(self.screen, (65, 49, 46), track)
            pygame.draw.rect(self.screen, ACCENT, (track.x, thumb_y, track.width, thumb_height))

    def _draw_selected_card(self, rect: pygame.Rect) -> None:
        """Keep the selected entity's identity and key state visible while the sidebar scrolls."""
        pygame.draw.rect(self.screen, (31, 25, 29), rect)
        pygame.draw.rect(self.screen, (116, 77, 62), rect, max(1, self.u(1)))
        left = rect.x + self.u(9)
        right = rect.right - self.u(9)
        y = rect.y + self.u(7)
        self.label("SELECTED OBJECT", (left, y), ACCENT, self.small_font)
        y += self.u(21)
        if not self.selected:
            self.label("Select a unit, building, or tile", (left, y), MUTED, self.small_font)
            return

        kind, entity = self.selected
        if kind == "tile":
            title = f"{entity.get('terrain', 'Terrain')} tile"
            subtitle = "MARTIAN SURFACE"
            position = entity.get("position", ("?", "?"))
            rows = [
                ("Region", entity.get("region", "Unknown")),
                ("Survey", "Explored" if entity.get("explored") else "Unsurveyed"),
                ("Deposits", ", ".join(entity.get("deposits", {})) or "None detected"),
            ]
        else:
            title = str(entity.get("name", kind.title()))
            category = str(entity.get("category", kind)).replace("_", " ").upper()
            subtitle = f"{category}  ·  ID {entity.get('id', '—')}"
            position = entity.get("position", ("?", "?"))
            if kind == "agent":
                health = entity.get("health")
                rows = [
                    ("Role", entity.get("profession") or entity.get("role") or "Unassigned"),
                    ("Activity", entity.get("current_activity") or entity.get("state") or "Idle"),
                    ("Health", f"{health:.0f}%" if isinstance(health, (int, float)) else "Unknown"),
                    ("Fatigue", f"{entity['fatigue']:.0f}%" if isinstance(entity.get("fatigue"), (int, float))
                     else "Unknown"),
                ]
                if entity.get("cargo"):
                    rows.append(("Cargo", self._display_value(entity["cargo"])))
            else:
                operational = entity.get("fully_operational")
                if operational is None:
                    operational = entity.get("enabled", True) and entity.get("powered", True)
                status = "Operational" if operational else "Needs attention"
                integrity = entity.get("integrity")
                rows = [
                    ("Status", status),
                    ("Power", "Offline" if entity.get("powered") is False else "Online"),
                    ("Condition", f"{integrity:.0f}%" if isinstance(integrity, (int, float))
                     else "Unknown"),
                    ("Upkeep", f"{entity['maintenance']:.0f}%"
                     if isinstance(entity.get("maintenance"), (int, float)) else "Unknown"),
                ]
                if entity.get("crop_stage"):
                    crop_health = entity.get("crop_health")
                    crop_health = crop_health if isinstance(crop_health, (int, float)) else 0
                    rows.append(("Crops", f"{entity['crop_stage']} · {crop_health:.0f}% health"))
                elif entity.get("storage"):
                    rows.append(("Storage", self._display_value(entity["storage"])))

        title = self._fit(title, right - left, self.font)
        self.label(title, (left, y), TEXT, self.font)
        y += self.u(19)
        self.label(self._fit(f"{subtitle}  ·  ({position[0]}, {position[1]})",
                             right - left, self.small_font), (left, y), MUTED, self.small_font)
        y += self.u(19)
        label_width = self.u(72)
        value_width = max(self.u(40), right - left - label_width)
        for label, value in rows[:5]:
            self.label(label.upper(), (left, y), MUTED, self.small_font)
            self.label(self._fit(self._display_value(value), value_width, self.small_font),
                       (left + label_width, y), TEXT, self.small_font)
            y += self.u(17)

    @staticmethod
    def _display_value(value) -> str:
        if isinstance(value, dict):
            return ", ".join(f"{name}: {amount:g}" if isinstance(amount, (int, float))
                              else f"{name}: {amount}" for name, amount in value.items()) or "None"
        if isinstance(value, (tuple, list)):
            return ", ".join(map(str, value)) or "None"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value)

    def _section(self, x, y, title):
        pygame.draw.line(self.screen, (91, 59, 53), (x, y + self.u(8)),
                         (self.screen.get_width() - self.u(16), y + self.u(8)), self.u(1))
        self.label(title, (x, y), ACCENT, self.small_font)

    @staticmethod
    def _fit(text: str, width: int, font: pygame.font.Font) -> str:
        text = str(text)
        if font.size(text)[0] <= width:
            return text
        while text and font.size(text + "…")[0] > width:
            text = text[:-1]
        return text + "…" if text else ""

    def _draw(self):
        width, _height, _side_w, viewport, panel = self._layout()
        paused_key = self._paused_frame_key(viewport)
        if self.paused and self.last_snapshot is not None and paused_key == self._last_paused_frame_key:
            self.paused_redraw_skips += 1
            return self.last_snapshot, viewport
        snapshot = self.simulation.world_snapshot()
        if not self.camera_centered:
            logical_size = (viewport.width // self.renderer.pixel_scale,
                            viewport.height // self.renderer.pixel_scale)
            self.camera.center_on((snapshot.width / 2, snapshot.height / 2), logical_size)
            self.camera_centered = True
        paused_key = self._paused_frame_key(viewport)
        self.last_snapshot = snapshot
        self._draw_header(width, snapshot)
        if self.research_mode:
            self._draw_research_screen(viewport, snapshot)
        elif self.crew_mode:
            self._draw_crew_screen(viewport, snapshot)
        else:
            self.renderer.draw(snapshot, viewport)
        if self.build_mode:
            self._draw_build_palette(viewport)
        self._draw_sidebar(panel, snapshot)
        if self.scenario_mode:
            self._draw_scenario_picker(viewport)
        pygame.display.flip()
        self._last_paused_frame_key = paused_key if self.paused else None
        return snapshot, viewport

    def _paused_frame_key(self, viewport: pygame.Rect) -> tuple:
        selected = None
        if self.selected:
            kind, entity = self.selected
            selected = (kind, entity.get("id", entity.get("position")))
        return (
            self.simulation.current_tick, id(self.screen), self.screen.get_size(), tuple(viewport),
            round(self.camera.x, 6), round(self.camera.y, 6), round(self.camera.zoom, 6),
            self.panel_scroll, self.crew_scroll, self.research_scroll, selected,
            self.crew_mode, self.research_mode, self.scenario_mode, self.build_mode,
            self.renderer.show_grid, self.renderer.show_exploration, self.renderer.show_minimap,
            self.renderer.quality, self.ui_scale, self.selected_building_type, self.build_message,
        )

    def _draw_scenario_picker(self, viewport: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, (24, 20, 24), viewport)
        pygame.draw.rect(self.screen, ACCENT, viewport, 2)
        self.label("NEW MISSION / SELECT A SCENARIO", (viewport.x + self.u(24), viewport.y + self.u(22)), ACCENT,
                   self.title_font)
        self.label("Each selection creates a new authoritative simulation with its own starting state.",
                   (viewport.x + self.u(24), viewport.y + self.u(56)), MUTED, self.small_font)
        descriptions = {
            "First Landing": "Small crew, lean stores, scheduled relief.",
            "Research Outpost": "Science team, laboratory and medical facilities.",
            "Industrial Base": "Robots, mine, workshop, storage and recycling.",
            "Survival": "Small stores and a compact crew.",
            "Sandbox": "Standard settlement with unrestricted scenario tuning in code.",
            "Established Settlement": "Larger crew, expanded stores and additional facilities.",
        }
        self.scenario_buttons = {}
        card_height = min(self.u(100), max(self.u(76), (viewport.height - self.u(142)) // 3))
        row_gap = self.u(10)
        for index, name in enumerate(descriptions):
            col, row = index % 2, index // 2
            rect = pygame.Rect(viewport.x + self.u(24) + col * (viewport.width // 2),
                               viewport.y + self.u(92) + row * (card_height + row_gap),
                               viewport.width // 2 - self.u(40), card_height)
            pygame.draw.rect(self.screen, (47, 37, 39), rect)
            pygame.draw.rect(self.screen, (120, 79, 63), rect, 2)
            self.label(name.upper(), (rect.x + self.u(12), rect.y + self.u(12)), CYAN)
            self._wrapped_label(descriptions[name], (rect.x + self.u(12), rect.y + self.u(38)),
                                rect.width - self.u(24), TEXT, self.small_font, line_gap=1)
            self.scenario_buttons[name] = rect
        self.label("ESC: RETURN TO COLONY", (viewport.x + self.u(24), viewport.bottom - self.u(30)), MUTED,
                   self.small_font)

    def _draw_research_screen(self, viewport: pygame.Rect, snapshot) -> None:
        pygame.draw.rect(self.screen, (28, 25, 28), viewport)
        self.label("RESEARCH / OPERATIONAL FACILITIES AND SCIENTISTS", (viewport.x + self.u(24), viewport.y + self.u(20)),
                   ACCENT, self.title_font)
        self.label("Queue a project. Progress requires a living scientist, an operational lab, and science points.",
                   (viewport.x + self.u(24), viewport.y + self.u(52)), MUTED, self.small_font)
        self.research_buttons = {}
        completed = {project.name for project in self.simulation.model.research_manager.completed_projects
                     if project.completed}
        card_height = self.u(86)
        row_gap = self.u(8)
        for index, (name, (description, points, benefit)) in enumerate(RESEARCH_PROJECTS.items()):
            col, row = index % 2, index // 2
            rect = pygame.Rect(viewport.x + self.u(24) + col * (viewport.width // 2),
                               viewport.y + self.u(86) + row * (card_height + row_gap),
                               viewport.width // 2 - self.u(40), card_height)
            self.research_buttons[name] = rect
            tree_node = RESEARCH_TECH_TREE[name]
            missing = sorted(set(tree_node["prerequisites"]) - completed)
            pygame.draw.rect(self.screen, (46, 36, 39), rect)
            pygame.draw.rect(self.screen, (108, 75, 62), rect, 1)
            heading = f"{tree_node['category'].upper()} / {name.upper()}"
            self.label(self._fit(heading, rect.width - self.u(20), self.small_font),
                       (rect.x + self.u(10), rect.y + self.u(6)), MUTED if missing else CYAN, self.small_font)
            self._wrapped_label(f"{description} ({points} pts)", (rect.x + self.u(10), rect.y + self.u(26)),
                                rect.width - self.u(20), TEXT, self.small_font, line_gap=0)
            unlock_text = f"LOCKED: {', '.join(missing)}" if missing else f"UNLOCK: {benefit}"
            self._wrapped_label(unlock_text, (rect.x + self.u(10), rect.y + self.u(56)),
                                rect.width - self.u(20), MUTED if missing else AMBER, self.small_font, line_gap=0)
        y = viewport.y + self.u(86) + 3 * (card_height + row_gap) + self.u(7) - self.research_scroll
        if self.research_message:
            self._wrapped_label(self.research_message, (viewport.x + self.u(24), y), viewport.width - self.u(48),
                                RED, self.small_font)
            y += self.u(28)
        self.label("PROJECT QUEUE", (viewport.x + self.u(24), y), ACCENT)
        y += self.u(24)
        projects = snapshot.telemetry.get("research_projects", ())
        if not projects:
            self.label("No projects queued.", (viewport.x + self.u(24), y), MUTED, self.small_font)
        self.screen.set_clip(viewport)
        for project in projects:
            scientist = project.get("scientist") or "Awaiting scientist and lab"
            line = (f"{project['status'].upper()}  {project['name']}  "
                    f"{project['progress']:.0f}/{project['required_points']:.0f}  {scientist}")
            y += self._wrapped_label(line, (viewport.x + self.u(24), y), viewport.width - self.u(48),
                                     GREEN if project["status"] == "Complete" else TEXT,
                                     self.small_font)
        self.screen.set_clip(None)
        content_bottom = y + self.research_scroll
        max_scroll = max(0, content_bottom - viewport.bottom + self.u(8))
        self.research_scroll = min(max(0, self.research_scroll), max_scroll)
        if max_scroll:
            track = pygame.Rect(viewport.right - self.u(7), viewport.y + self.u(8),
                                self.u(3), viewport.height - self.u(16))
            thumb_height = max(self.u(24), round(track.height * viewport.height / (content_bottom - viewport.y)))
            thumb_y = track.y + round((track.height - thumb_height) * self.research_scroll / max_scroll)
            pygame.draw.rect(self.screen, (65, 49, 46), track)
            pygame.draw.rect(self.screen, ACCENT, (track.x, thumb_y, track.width, thumb_height))

    def _draw_build_palette(self, viewport: pygame.Rect) -> None:
        choices = ("SolarArray", "Habitat", "Greenhouse", "OxygenGenerator", "WaterPlant",
                   "Battery", "Laboratory", "Workshop", "MedicalBay", "Mine", "FuelDepot",
                   "WaterReservoir", "FoodWarehouse", "OxygenStorageFacility", "MaterialsWarehouse")
        panel = pygame.Rect(viewport.x + self.u(12), viewport.y + self.u(12), self.u(190),
                            min(viewport.height - self.u(24), self.u(500)))
        pygame.draw.rect(self.screen, PANEL, panel)
        pygame.draw.rect(self.screen, ACCENT, panel, self.u(2))
        self.label("BUILD / SELECT TYPE", (panel.x + self.u(10), panel.y + self.u(10)), ACCENT, self.small_font)
        self.build_palette = {}
        for index, name in enumerate(choices):
            rect = pygame.Rect(panel.x + self.u(8), panel.y + self.u(34 + index * 30),
                               panel.width - self.u(16), self.u(26))
            self.build_palette[name] = rect
            selected = name == self.selected_building_type
            pygame.draw.rect(self.screen, (75, 49, 42) if selected else PANEL_DARK, rect)
            pygame.draw.rect(self.screen, ACCENT if selected else (83, 66, 59), rect, self.u(1))
            self.label(name.upper(), (rect.x + self.u(7), rect.y + self.u(8)), TEXT, self.small_font)
        self.label(self._fit(self.build_message or f"Click map to place {self.selected_building_type}.",
                             panel.width - self.u(20), self.small_font),
                   (panel.x + self.u(10), panel.bottom - self.u(30)),
                   AMBER, self.small_font)
        y = panel.bottom + self.u(8)
        for project in self.last_snapshot.telemetry.get("construction_projects", ()):
            self.label(self._fit(f"{project['status']} {project['name']} {project['progress']:.0f}%",
                                 panel.width - self.u(20), self.small_font),
                       (panel.x + self.u(8), y), TEXT, self.small_font)
            y += self.u(16)

    def advance_frame(self, elapsed: float) -> int:
        """Advance the existing simulation using its normal tick method."""
        if self.paused:
            return 0
        self.accumulator += min(max(0.0, elapsed), .25) * self.simulation.simulation_speed
        ticks = 0
        while self.accumulator >= .25:
            self.simulation.step()
            self.accumulator -= .25
            ticks += 1
        return ticks

    def _toggle_pause(self):
        self.paused = not self.paused
        self.simulation.toggle_pause()

    def handle_event(self, event, snapshot=None, viewport=None):
        """Process an input event; factored out to make controls testable."""
        self._last_paused_frame_key = None
        if viewport is None:
            _width, _height, _side, viewport, _panel = self._layout()
        snapshot = snapshot or self.last_snapshot or self.simulation.world_snapshot()
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            center = self._camera_center()
            self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            self.renderer.screen = self.screen
            self.windowed_size = self.screen.get_size()
            if not self._ui_scale_explicit:
                self.ui_scale = self._display_dpi_scale(self.screen.get_size())
                self._apply_ui_scale()
            self.display_settings = DisplaySettings(width=self.screen.get_width(), height=self.screen.get_height(),
                fullscreen=False, quality=self.renderer.quality,
                ui_scale=self.ui_scale if self._ui_scale_explicit else None)
            if hasattr(pygame.display, "set_minimum_size"):
                pygame.display.set_minimum_size((self.u(960), self.u(640)))
            _width, _height, _side, resized_viewport, _panel = self._layout()
            self.camera.center_on(center, resized_viewport.size)
        elif event.type == getattr(pygame, "WINDOWDISPLAYCHANGED", -1):
            center = self._camera_center()
            if not self._ui_scale_explicit:
                self.ui_scale = self._display_dpi_scale(self.screen.get_size())
                self._apply_ui_scale()
            self.display_settings = DisplaySettings(width=self.screen.get_width(),
                height=self.screen.get_height(), fullscreen=self.fullscreen,
                quality=self.renderer.quality,
                ui_scale=self.ui_scale if self._ui_scale_explicit else None)
            _width, _height, _side, resized_viewport, _panel = self._layout()
            self.camera.center_on(center, resized_viewport.size)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.scenario_mode or self.research_mode or self.build_mode:
                    self.scenario_mode = False
                    self.research_mode = False
                    self.build_mode = False
                else:
                    self.running = False
            elif event.key == pygame.K_SPACE:
                self._toggle_pause()
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self._change_speed(1)
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self._change_speed(-1)
            elif event.key == pygame.K_PERIOD and self.paused:
                self.simulation.step_once()
            elif event.key == pygame.K_g:
                self.renderer.show_grid = not self.renderer.show_grid
            elif event.key == pygame.K_e:
                self.renderer.show_exploration = not self.renderer.show_exploration
            elif event.key == pygame.K_m:
                self.renderer.show_minimap = not self.renderer.show_minimap
            elif event.key == pygame.K_c:
                self.crew_mode = not self.crew_mode
            elif event.key == pygame.K_r:
                self.research_mode = not self.research_mode
                self.scenario_mode = False
                self.crew_mode = False
            elif event.key == pygame.K_b:
                self.build_mode = not self.build_mode
                self.scenario_mode = False
                self.research_mode = False
                self.crew_mode = False
            elif event.key == pygame.K_F11:
                self.toggle_fullscreen()
            elif event.key == pygame.K_F1:
                qualities = tuple(QUALITY_PRESETS)
                current = qualities.index(self.renderer.quality)
                self.set_quality(qualities[(current + 1) % len(qualities)])
        elif event.type == pygame.MOUSEWHEEL:
            pointer = pygame.mouse.get_pos()
            if not self.last_viewport.collidepoint(pointer):
                self.panel_scroll = max(0, self.panel_scroll - event.y * self.u(48))
            elif self.research_mode and self.last_viewport.collidepoint(pointer):
                self.research_scroll = max(0, self.research_scroll - event.y * self.u(40))
            elif self.crew_mode:
                self.crew_scroll = max(0, self.crew_scroll - event.y * self.u(60))
            else:
                self.camera.zoom_at(1.12 if event.y > 0 else 1 / 1.12, pointer)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                key = next((name for name, rect in self.buttons.items() if rect.collidepoint(event.pos)), None)
                if key:
                    self._activate_button(key)
                elif self.scenario_mode:
                    scenario = next((name for name, rect in getattr(self, "scenario_buttons", {}).items()
                                     if rect.collidepoint(event.pos)), None)
                    if scenario:
                        self._start_scenario(scenario)
                elif self.research_mode:
                    project_name = next((name for name, rect in getattr(self, "research_buttons", {}).items()
                                         if rect.collidepoint(event.pos)), None)
                    if project_name:
                        manager = self.simulation.model.research_manager
                        existing = [project.name for project in manager.research_queue]
                        existing += [project.name for project in manager.active_projects]
                        existing += [project.name for project in manager.completed_projects]
                        if project_name not in existing:
                            description, points, _benefit = RESEARCH_PROJECTS[project_name]
                            try:
                                manager.create_project(project_name, description, points, priority=2)
                                self.research_message = ""
                            except ValueError as error:
                                self.research_message = str(error)
                elif self.build_mode:
                    selected = next((name for name, rect in self.build_palette.items()
                                     if rect.collidepoint(event.pos)), None)
                    if selected:
                        self.selected_building_type = selected
                    elif viewport.collidepoint(event.pos):
                        picked = self.renderer.pick(snapshot, event.pos, viewport)
                        if picked and picked[0] == "tile":
                            try:
                                project = self.simulation.model.queue_construction(
                                    self.selected_building_type, tuple(picked[1]["position"]))
                                self.build_message = f"Queued {project.building_name} at {project.position}."
                            except ValueError as error:
                                self.build_message = str(error)
                elif viewport.collidepoint(event.pos):
                    row = next((entity for rect, entity in self.crew_rows if rect.collidepoint(event.pos)), None)
                    if self.crew_mode and row is not None:
                        self._select(("agent", row))
                    elif self.crew_mode:
                        self._handle_crew_control(event.pos)
                    elif not self.renderer.center_from_minimap(snapshot, event.pos, viewport):
                        if self.renderer.minimap_rect(viewport) is not None and self.renderer.minimap_rect(viewport).collidepoint(event.pos):
                            self.drag = None
                        else:
                            self.drag = event.pos
            elif event.button == 3 and viewport.collidepoint(event.pos):
                self._select(self.renderer.pick(snapshot, event.pos, viewport))
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag:
            if self.drag == event.pos:
                self._select(self.renderer.pick(snapshot, event.pos, viewport))
            self.drag = None
        elif event.type == pygame.MOUSEMOTION and self.drag:
            dx, dy = event.rel
            self.camera.x -= dx / (self.renderer.pixel_scale * self.camera.cell)
            self.camera.y -= dy / (self.renderer.pixel_scale * self.camera.cell)

    def _draw_crew_screen(self, viewport: pygame.Rect, snapshot) -> None:
        self.screen.set_clip(viewport)
        pygame.draw.rect(self.screen, (28, 25, 28), viewport)
        x, y = viewport.x + self.u(20), viewport.y + self.u(18)
        self.label("CREW ROSTER / PERSONNEL FILES", (x, y), ACCENT, self.title_font)
        y += self.u(34)
        self.label("Click a crew record to inspect identity, needs, skills, work and relationships.",
                   (x, y), MUTED, self.small_font)
        y += self.u(30)
        controls = [("filter", f"FILTER: {self.crew_filter.upper()}"),
                    ("sort", f"SORT: {self.crew_sort.upper()}")]
        self.crew_control_rects = {}
        for index, (key, text) in enumerate(controls):
            rect = pygame.Rect(x + index * self.u(170), y, self.u(156), self.u(30))
            self.crew_control_rects[key] = rect
            pygame.draw.rect(self.screen, (48, 37, 39), rect)
            pygame.draw.rect(self.screen, (120, 79, 63), rect, self.u(1))
            self.label(text, (rect.x + self.u(8), rect.y + self.u(9)), TEXT, self.small_font)
        y += self.u(42)
        people = [agent for agent in snapshot.agents
                  if self.crew_filter == "all"
                  or self.crew_filter == "robots" and agent["category"] == "robot"
                  or self.crew_filter == "astronauts" and agent["category"] == "agent"]
        sort_key = {"name": lambda item: item["name"].casefold(),
                    "health": lambda item: -float(item.get("health", 0)),
                    "profession": lambda item: (item.get("profession", ""), item["name"])}[self.crew_sort]
        people.sort(key=sort_key)
        self.crew_rows = []
        available_height = max(0, viewport.bottom - y - self.u(12))
        row_height = self.u(72)
        max_scroll = max(0, len(people) * row_height - available_height)
        self.crew_scroll = min(self.crew_scroll, max_scroll)
        self.screen.set_clip(pygame.Rect(viewport.x, y, viewport.width, available_height))
        for index, agent in enumerate(people):
            rect = pygame.Rect(x, y + index * row_height - self.crew_scroll,
                               viewport.width - self.u(40), row_height - self.u(4))
            if rect.bottom < y or rect.top > viewport.bottom:
                continue
            selected = self.selected is not None and self.selected[0] == "agent" and self.selected[1].get("id") == agent["id"]
            pygame.draw.rect(self.screen, (54, 40, 40) if selected else (37, 32, 34), rect)
            pygame.draw.rect(self.screen, ACCENT if selected else (77, 60, 55), rect, self.u(1))
            robot = agent["category"] == "robot"
            source = character_sprite(robot, 0, 2, False, agent.get("appearance", {}), "idle",
                                      self.renderer.quality_options["sprite_detail"])
            portrait_size = (self.u(38), self.u(46)) if not robot else (self.u(50), self.u(42))
            portrait = pygame.transform.scale(source, portrait_size)
            self.screen.blit(portrait, (rect.x + self.u(7), rect.y + self.u(8)))
            self.label(agent["name"], (rect.x + self.u(58), rect.y + self.u(8)), TEXT)
            self.label(agent.get("profession", "Robot" if robot else "Crew"),
                       (rect.x + self.u(58), rect.y + self.u(28)), CYAN, self.small_font)
            activity = agent.get("current_activity", agent.get("state", "Idle"))
            self.label(self._fit(str(activity), self.u(190), self.small_font),
                       (rect.x + self.u(58), rect.y + self.u(46)), MUTED, self.small_font)
            meter_color = GREEN if agent.get("alive", True) else RED
            self._draw_meter(pygame.Rect(rect.right - self.u(106), rect.y + self.u(14),
                                         self.u(88), self.u(7)), agent.get("health", 0), meter_color)
            self.label(f"HP {agent.get('health', 0):.0f}", (rect.right - self.u(106), rect.y + self.u(28)),
                       meter_color, self.small_font)
            needs = f"H {agent.get('hunger', 0):.0f}  T {agent.get('thirst', 0):.0f}  F {agent.get('fatigue', 0):.0f}"
            self.label(needs, (rect.right - self.u(106), rect.y + self.u(46)), MUTED, self.small_font)
            self.crew_rows.append((rect, agent))
        self.screen.set_clip(None)

    def _handle_crew_control(self, point):
        rects = getattr(self, "crew_control_rects", {})
        if rects.get("filter") and rects["filter"].collidepoint(point):
            options = ("all", "astronauts", "robots")
            self.crew_filter = options[(options.index(self.crew_filter) + 1) % len(options)]
        elif rects.get("sort") and rects["sort"].collidepoint(point):
            options = ("name", "health", "profession")
            self.crew_sort = options[(options.index(self.crew_sort) + 1) % len(options)]

    def _select(self, picked):
        self.selected = picked
        if picked and picked[0] in {"agent", "building"}:
            self.renderer.selected = (picked[0], picked[1]["id"])
        else:
            self.renderer.selected = None

    def _change_speed(self, delta: int):
        self.speed_index = max(0, min(len(self.speed_levels) - 1, self.speed_index + delta))
        self.simulation.set_speed(self.speed_levels[self.speed_index])

    def _activate_button(self, key: str):
        if key == "pause":
            self._toggle_pause()
        elif key == "slower":
            self._change_speed(-1)
        elif key == "faster":
            self._change_speed(1)
        elif key == "step" and self.paused:
            self.simulation.step_once()
        elif key == "grid":
            self.renderer.show_grid = not self.renderer.show_grid
        elif key == "map":
            self.renderer.show_minimap = not self.renderer.show_minimap
        elif key == "crew":
            self.crew_mode = not self.crew_mode
        elif key == "new":
            self.scenario_mode = not self.scenario_mode
            self.research_mode = False
        elif key == "research":
            self.research_mode = not self.research_mode
            self.scenario_mode = False
            self.crew_mode = False

    def _start_scenario(self, name: str) -> None:
        seed = self.simulation.config.seed
        self.simulation.stop()
        self.simulation = Simulation(config=ColonyConfig.preset(name, seed=seed))
        self.simulation.start()
        self.renderer = Renderer(self.screen, self.camera, seed,
                                 quality=self.display_settings.quality, ui_scale=self.ui_scale)
        self.camera_centered = False
        self.selected = None
        self.crew_mode = False
        self.scenario_mode = False

    def run(self):
        try:
            while self.running:
                elapsed = self.clock.tick(60) / 1000.0
                snapshot, viewport = self._draw()
                for event in pygame.event.get():
                    self.handle_event(event, snapshot, viewport)
                self.advance_frame(elapsed)
        finally:
            self.simulation.stop()
            pygame.quit()


def main():
    HabrynApp().run()
