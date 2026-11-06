"""Retro pixel-art Mission Control interface for Habryn."""
from __future__ import annotations

import pygame

from colony.simulation import Simulation
from colony.initialization import ColonyConfig
from colony.visualization.pixel_art import character_sprite
from colony.visualization.renderer import Camera, Renderer

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
    def __init__(self, simulation: Simulation | None = None, size=(1280, 800)):
        pygame.init()
        pygame.display.set_caption("HABRYN // MARS COLONY MISSION CONTROL")
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        if hasattr(pygame.display, "set_minimum_size"):
            pygame.display.set_minimum_size((960, 640))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 12, bold=True)
        self.title_font = pygame.font.SysFont("monospace", 20, bold=True)
        self.simulation = simulation or Simulation()
        self.simulation.start()
        self.camera = Camera()
        self.camera_centered = False
        self.renderer = Renderer(self.screen, self.camera, self.simulation.config.seed)
        self.paused = False
        self.accumulator = 0.0
        self.drag: tuple[int, int] | None = None
        self.selected: tuple[str, object] | None = None
        self.panel_scroll = 0
        self.panel_content_height = 0
        self.running = True
        self.speed_levels = (.25, .5, 1.0, 2.0, 4.0, 8.0)
        self.speed_index = 2
        self.crew_mode = False
        self.crew_filter = "all"
        self.crew_sort = "name"
        self.crew_scroll = 0
        self.crew_rows: list[tuple[pygame.Rect, object]] = []
        self.buttons: dict[str, pygame.Rect] = {}
        self.last_viewport = pygame.Rect(0, HEADER_HEIGHT, 1, 1)
        self.last_snapshot = None
        self.scenario_mode = False
        self.research_mode = False
        self.build_mode = False
        self.selected_building_type = "SolarArray"
        self.build_message = ""
        self.build_palette = {}

    def label(self, text, position, color=TEXT, font=None):
        font = font or self.font
        self.screen.blit(font.render(str(text), False, color), position)

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
        side_w = min(SIDEBAR_WIDTH, max(280, width // 3))
        panel = pygame.Rect(width - side_w, HEADER_HEIGHT, side_w, height - HEADER_HEIGHT)
        viewport = pygame.Rect(0, HEADER_HEIGHT, panel.x, height - HEADER_HEIGHT)
        self.last_viewport = viewport
        return width, height, side_w, viewport, panel

    def _draw_header(self, width: int, snapshot):
        pygame.draw.rect(self.screen, (42, 28, 33), (0, 0, width, HEADER_HEIGHT))
        pygame.draw.line(self.screen, ACCENT, (0, HEADER_HEIGHT - 2), (width, HEADER_HEIGHT - 2), 2)
        self.label(self._fit(self.simulation.config.colony_name.upper(), 160, self.title_font),
                   (18, 10), ACCENT, self.title_font)
        self.label(self._fit(f"MARS / {self.simulation.config.colony_id}", 160, self.small_font),
                   (20, 38), MUTED, self.small_font)
        self.label(snapshot.time.upper(), (194, 15), CYAN)
        self.label(f"TICK {snapshot.tick:07d}", (194, 37), MUTED, self.small_font)
        self.buttons.clear()
        x = max(380, width - 630)
        self._button("pause", (x, 13, 78, 36), "RESUME" if self.paused else "PAUSE", active=self.paused)
        self._button("slower", (x + 86, 13, 34, 36), "−")
        self.label(f"{self.simulation.simulation_speed:g}X", (x + 126, 23), TEXT, self.small_font)
        self._button("faster", (x + 166, 13, 34, 36), "+")
        self._button("step", (x + 208, 13, 60, 36), "STEP", active=self.paused)
        self._button("grid", (x + 276, 13, 48, 36), "GRID", active=self.renderer.show_grid)
        self._button("map", (x + 332, 13, 48, 36), "MAP", active=self.renderer.show_minimap)
        self._button("crew", (x + 388, 13, 60, 36), "CREW", active=self.crew_mode)
        self._button("new", (x + 454, 13, 60, 36), "NEW", active=self.scenario_mode)
        self._button("research", (x + 520, 13, 60, 36), "R&D", active=self.research_mode)

    def _draw_meter(self, rect, percentage: float, color):
        pygame.draw.rect(self.screen, (25, 23, 26), rect)
        pygame.draw.rect(self.screen, (86, 66, 58), rect, 1)
        amount = int((rect.width - 2) * max(0, min(100, percentage)) / 100)
        if amount:
            pygame.draw.rect(self.screen, color, (rect.x + 1, rect.y + 1, amount, rect.height - 2))

    def _draw_sidebar(self, panel: pygame.Rect, snapshot):
        pygame.draw.rect(self.screen, PANEL, panel)
        pygame.draw.line(self.screen, (116, 77, 62), panel.topleft, (panel.x, panel.bottom), 2)
        self.screen.set_clip(panel)
        left = panel.x + 16
        right = panel.right - 16
        y = panel.y + 14 - self.panel_scroll
        self.label("COLONY / STATUS", (left, y), ACCENT, self.font)
        y += 27
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
        colw = (panel.width - 40) // 2
        for index, (name, value) in enumerate(facts):
            col = index % 2
            row = index // 2
            xx, yy = left + col * colw, y + row * 34
            self.label(name, (xx, yy), MUTED, self.small_font)
            self.label(value, (xx, yy + 13), TEXT)
        y += ((len(facts) + 1) // 2) * 34 + 10

        warnings = telemetry.get("warnings", ())
        if warnings:
            self.label("! RESOURCE WARNING", (left, y), RED)
            y += 19
            warning_text = ", ".join(warnings)
            self.label(self._fit(warning_text, right - left, self.small_font), (left, y), RED, self.small_font)
            y += 21

        self._section(left, y, "RESOURCE STORES")
        y += 24
        resources = telemetry.get("resource_inventory", {})
        for name, value in resources.items():
            amount, capacity = value["current_amount"], value["storage_capacity"]
            fill = value["fill_percentage"]
            color = RED if name in warnings or fill < 20 else CYAN if name in {"Power", "Oxygen", "Water"} else GREEN
            self.label(name.upper(), (left, y), TEXT, self.small_font)
            value_text = f"{amount:,.0f}/{capacity:,.0f} {value['unit']}"
            self.label(value_text, (right - self.font.size(value_text)[0], y), MUTED, self.small_font)
            y += 17
            self._draw_meter(pygame.Rect(left, y, right - left, 6), fill, color)
            y += 13

        y += 3
        self._section(left, y, "INFRASTRUCTURE")
        y += 24
        for building in snapshot.buildings:
            kind = building.get("category", building.get("name", "Facility"))
            name = self._fit(building.get("name", kind), right - left - 65, self.small_font)
            integrity = building.get("integrity", 100)
            if building.get("powered") is False:
                status, color = "NO PWR", RED
            elif not building.get("enabled", True):
                status, color = "OFF", MUTED
            elif integrity is not None and integrity < 60:
                status, color = "DAMAGED", AMBER
            else:
                status, color = "ONLINE", GREEN
            self.label(name, (left, y), TEXT, self.small_font)
            self.label(status, (right - self.small_font.size(status)[0], y), color, self.small_font)
            y += 19

        y += 4
        self._section(left, y, "RECENT EVENTS")
        y += 24
        events = telemetry.get("events_feed", ())[-4:]
        if events:
            for event in events:
                self.label(self._fit(event.get("name", "Colony event"), right - left, self.small_font),
                           (left, y), AMBER, self.small_font)
                y += 16
                self.label(self._fit(event.get("description", ""), right - left, self.small_font),
                           (left, y), MUTED, self.small_font)
                y += 19
        else:
            self.label("NO ACTIVE ALERTS", (left, y), MUTED, self.small_font)
            y += 18

        y += 3
        self._section(left, y, "CREW COMMS")
        y += 22
        conversations = telemetry.get("conversations", ())
        relevant = [item for item in conversations if not self.selected or self.selected[0] != "agent"
                    or self.selected[1].get("id") in item.get("participants", ())]
        recent = relevant[-2:]
        if recent:
            for conversation in recent:
                for turn in conversation.get("turns", ())[-2:]:
                    line = f"{turn.get('speaker', 'Crew')}: {turn.get('text', '')}"
                    self.label(self._fit(line, right - left, self.small_font), (left, y), CYAN, self.small_font)
                    y += 16
        else:
            self.label("NO RECENT CONVERSATIONS", (left, y), MUTED, self.small_font)
            y += 17

        y += 5
        self._section(left, y, "SELECTED OBJECT")
        y += 24
        if self.selected:
            kind, entity = self.selected
            if kind == "tile":
                details = [("TYPE", "MARTIAN TERRAIN"), ("POSITION", entity["position"]),
                           ("TERRAIN", entity.get("terrain", "Unknown")),
                           ("EXPLORED", "YES" if entity.get("explored") else "NO")]
                if entity.get("deposits"):
                    details.append(("DEPOSITS", ", ".join(entity["deposits"])))
            else:
                if kind == "agent":
                    robot = entity.get("category") == "robot"
                    portrait = character_sprite(robot, 0, 2, False, entity.get("appearance", {}), "idle")
                    portrait_height = 64 if not robot else 56
                    portrait_width = 48 if not robot else 64
                    portrait = pygame.transform.scale(portrait, (portrait_width, portrait_height))
                    self.screen.blit(portrait, (left, y))
                    self.label(entity.get("name", "CREW MEMBER"), (left + portrait_width + 10, y + 8), TEXT)
                    self.label(entity.get("profession", "Specialist"), (left + portrait_width + 10, y + 27), CYAN,
                               self.small_font)
                    self.label(f"HEALTH {entity.get('health', 0):.0f}%", (left + portrait_width + 10, y + 45),
                               GREEN if entity.get("alive") else RED, self.small_font)
                    y += portrait_height + 8
                details = [("TYPE", kind.upper()), ("NAME", entity.get("name", kind)),
                           ("ID", entity.get("id")), ("POSITION", entity.get("position"))]
                for attr in ("profession", "specialization", "state", "current_activity", "next_activity",
                             "decision_reason", "alive", "health", "moving", "destination", "busy", "powered",
                             "integrity", "social_need", "recreation_need", "work_schedule", "skills", "personality"):
                    if attr in entity and entity[attr] is not None:
                        details.append((attr.upper(), entity[attr]))
            for key, value in details[:10]:
                self.label(key, (left, y), MUTED, self.small_font)
                value_text = self._fit(str(value), right - left - 84, self.small_font)
                self.label(value_text, (left + 84, y), TEXT, self.small_font)
                y += 18
        else:
            self.label("CLICK A UNIT OR STRUCTURE", (left, y), MUTED, self.small_font)
            y += 18

        self.panel_content_height = y + self.panel_scroll - panel.y
        max_scroll = max(0, self.panel_content_height - panel.height + 12)
        self.panel_scroll = min(self.panel_scroll, max_scroll)
        self.screen.set_clip(None)

    def _section(self, x, y, title):
        pygame.draw.line(self.screen, (91, 59, 53), (x, y + 8), (self.screen.get_width() - 16, y + 8), 1)
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
        self.screen.fill(BG)
        width, _height, _side_w, viewport, panel = self._layout()
        snapshot = self.simulation.world_snapshot()
        if not self.camera_centered:
            logical_size = (viewport.width // self.renderer.pixel_scale,
                            viewport.height // self.renderer.pixel_scale)
            self.camera.center_on((snapshot.width / 2, snapshot.height / 2), logical_size)
            self.camera_centered = True
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
        return snapshot, viewport

    def _draw_scenario_picker(self, viewport: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, (24, 20, 24), viewport)
        pygame.draw.rect(self.screen, ACCENT, viewport, 2)
        self.label("NEW MISSION / SELECT A SCENARIO", (viewport.x + 24, viewport.y + 22), ACCENT,
                   self.title_font)
        self.label("Each selection creates a new authoritative simulation with its own starting state.",
                   (viewport.x + 24, viewport.y + 56), MUTED, self.small_font)
        descriptions = {
            "First Landing": "Small crew, lean stores, scheduled relief.",
            "Research Outpost": "Science team, laboratory and medical facilities.",
            "Industrial Base": "Robots, mine, workshop, storage and recycling.",
            "Survival": "Small stores and a compact crew.",
            "Sandbox": "Standard settlement with unrestricted scenario tuning in code.",
            "Established Settlement": "Larger crew, expanded stores and additional facilities.",
        }
        self.scenario_buttons = {}
        for index, name in enumerate(descriptions):
            col, row = index % 2, index // 2
            rect = pygame.Rect(viewport.x + 24 + col * (viewport.width // 2),
                               viewport.y + 102 + row * 104, viewport.width // 2 - 40, 84)
            pygame.draw.rect(self.screen, (47, 37, 39), rect)
            pygame.draw.rect(self.screen, (120, 79, 63), rect, 2)
            self.label(name.upper(), (rect.x + 12, rect.y + 12), CYAN)
            self.label(self._fit(descriptions[name], rect.width - 24, self.small_font),
                       (rect.x + 12, rect.y + 40), TEXT, self.small_font)
            self.scenario_buttons[name] = rect
        self.label("ESC: RETURN TO COLONY", (viewport.x + 24, viewport.bottom - 30), MUTED,
                   self.small_font)

    def _draw_research_screen(self, viewport: pygame.Rect, snapshot) -> None:
        pygame.draw.rect(self.screen, (28, 25, 28), viewport)
        self.label("RESEARCH / OPERATIONAL FACILITIES AND SCIENTISTS", (viewport.x + 24, viewport.y + 20),
                   ACCENT, self.title_font)
        self.label("Queue a project. Progress requires a living scientist, an operational lab, and science points.",
                   (viewport.x + 24, viewport.y + 52), MUTED, self.small_font)
        self.research_buttons = {}
        for index, (name, (description, points, benefit)) in enumerate(RESEARCH_PROJECTS.items()):
            col, row = index % 2, index // 2
            rect = pygame.Rect(viewport.x + 24 + col * (viewport.width // 2),
                               viewport.y + 88 + row * 78, viewport.width // 2 - 40, 66)
            self.research_buttons[name] = rect
            pygame.draw.rect(self.screen, (46, 36, 39), rect)
            pygame.draw.rect(self.screen, (108, 75, 62), rect, 1)
            self.label(name.upper(), (rect.x + 10, rect.y + 6), CYAN)
            self.label(self._fit(f"{description} ({points} pts)", rect.width - 20, self.small_font),
                       (rect.x + 10, rect.y + 27), TEXT, self.small_font)
            self.label(self._fit(f"UNLOCK: {benefit}", rect.width - 20, self.small_font),
                       (rect.x + 10, rect.y + 45), AMBER, self.small_font)
        y = viewport.y + 344
        self.label("PROJECT QUEUE", (viewport.x + 24, y), ACCENT)
        y += 24
        projects = snapshot.telemetry.get("research_projects", ())
        if not projects:
            self.label("No projects queued.", (viewport.x + 24, y), MUTED, self.small_font)
        for project in projects[:8]:
            scientist = project.get("scientist") or "Awaiting scientist and lab"
            line = (f"{project['status'].upper()}  {project['name']}  "
                    f"{project['progress']:.0f}/{project['required_points']:.0f}  {scientist}")
            self.label(self._fit(line, viewport.width - 48, self.small_font), (viewport.x + 24, y),
                       GREEN if project["status"] == "Complete" else TEXT, self.small_font)
            y += 19

    def _draw_build_palette(self, viewport: pygame.Rect) -> None:
        choices = ("SolarArray", "Habitat", "Greenhouse", "OxygenGenerator", "WaterPlant",
                   "Battery", "Laboratory", "Workshop", "MedicalBay", "Mine")
        panel = pygame.Rect(viewport.x + 12, viewport.y + 12, 190, min(viewport.height - 24, 500))
        pygame.draw.rect(self.screen, PANEL, panel)
        pygame.draw.rect(self.screen, ACCENT, panel, 2)
        self.label("BUILD / SELECT TYPE", (panel.x + 10, panel.y + 10), ACCENT, self.small_font)
        self.build_palette = {}
        for index, name in enumerate(choices):
            rect = pygame.Rect(panel.x + 8, panel.y + 34 + index * 34, panel.width - 16, 29)
            self.build_palette[name] = rect
            selected = name == self.selected_building_type
            pygame.draw.rect(self.screen, (75, 49, 42) if selected else PANEL_DARK, rect)
            pygame.draw.rect(self.screen, ACCENT if selected else (83, 66, 59), rect, 1)
            self.label(name.upper(), (rect.x + 7, rect.y + 8), TEXT, self.small_font)
        self.label(self._fit(self.build_message or f"Click map to place {self.selected_building_type}.",
                             panel.width - 20, self.small_font), (panel.x + 10, panel.bottom - 30),
                   AMBER, self.small_font)
        y = panel.bottom + 8
        for project in self.last_snapshot.telemetry.get("construction_projects", ())[:2]:
            self.label(self._fit(f"{project['status']} {project['name']} {project['progress']:.0f}%",
                                 panel.width - 20, self.small_font), (panel.x + 8, y), TEXT, self.small_font)
            y += 16

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
        if viewport is None:
            _width, _height, _side, viewport, _panel = self._layout()
        snapshot = snapshot or self.last_snapshot or self.simulation.world_snapshot()
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            if hasattr(pygame.display, "set_minimum_size"):
                pygame.display.set_minimum_size((960, 640))
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
        elif event.type == pygame.MOUSEWHEEL:
            pointer = pygame.mouse.get_pos()
            if pointer[0] >= self.screen.get_width() - SIDEBAR_WIDTH:
                self.panel_scroll = max(0, self.panel_scroll - event.y * 48)
            elif self.crew_mode:
                self.crew_scroll = max(0, self.crew_scroll - event.y * 60)
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
                            manager.create_project(project_name, description, points, priority=2)
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
        x, y = viewport.x + 20, viewport.y + 18
        self.label("CREW ROSTER / PERSONNEL FILES", (x, y), ACCENT, self.title_font)
        y += 34
        self.label("Click a crew record to inspect identity, needs, skills, work and relationships.",
                   (x, y), MUTED, self.small_font)
        y += 30
        controls = [("filter", f"FILTER: {self.crew_filter.upper()}"),
                    ("sort", f"SORT: {self.crew_sort.upper()}")]
        self.crew_control_rects = {}
        for index, (key, text) in enumerate(controls):
            rect = pygame.Rect(x + index * 170, y, 156, 30)
            self.crew_control_rects[key] = rect
            pygame.draw.rect(self.screen, (48, 37, 39), rect)
            pygame.draw.rect(self.screen, (120, 79, 63), rect, 1)
            self.label(text, (rect.x + 8, rect.y + 9), TEXT, self.small_font)
        y += 42
        people = [agent for agent in snapshot.agents
                  if self.crew_filter == "all"
                  or self.crew_filter == "robots" and agent["category"] == "robot"
                  or self.crew_filter == "astronauts" and agent["category"] == "agent"]
        sort_key = {"name": lambda item: item["name"].casefold(),
                    "health": lambda item: -float(item.get("health", 0)),
                    "profession": lambda item: (item.get("profession", ""), item["name"])}[self.crew_sort]
        people.sort(key=sort_key)
        self.crew_rows = []
        available_height = max(0, viewport.bottom - y - 12)
        row_height = 72
        max_scroll = max(0, len(people) * row_height - available_height)
        self.crew_scroll = min(self.crew_scroll, max_scroll)
        self.screen.set_clip(pygame.Rect(viewport.x, y, viewport.width, available_height))
        for index, agent in enumerate(people):
            rect = pygame.Rect(x, y + index * row_height - self.crew_scroll, viewport.width - 40, row_height - 4)
            if rect.bottom < y or rect.top > viewport.bottom:
                continue
            selected = self.selected is not None and self.selected[0] == "agent" and self.selected[1].get("id") == agent["id"]
            pygame.draw.rect(self.screen, (54, 40, 40) if selected else (37, 32, 34), rect)
            pygame.draw.rect(self.screen, ACCENT if selected else (77, 60, 55), rect, 1)
            robot = agent["category"] == "robot"
            source = character_sprite(robot, 0, 2, False, agent.get("appearance", {}), "idle")
            portrait_size = (38, 46) if not robot else (50, 42)
            portrait = pygame.transform.scale(source, portrait_size)
            self.screen.blit(portrait, (rect.x + 7, rect.y + 8))
            self.label(agent["name"], (rect.x + 58, rect.y + 8), TEXT)
            self.label(agent.get("profession", "Robot" if robot else "Crew"),
                       (rect.x + 58, rect.y + 28), CYAN, self.small_font)
            activity = agent.get("current_activity", agent.get("state", "Idle"))
            self.label(self._fit(str(activity), 190, self.small_font), (rect.x + 58, rect.y + 46), MUTED, self.small_font)
            meter_color = GREEN if agent.get("alive", True) else RED
            self._draw_meter(pygame.Rect(rect.right - 106, rect.y + 14, 88, 7), agent.get("health", 0), meter_color)
            self.label(f"HP {agent.get('health', 0):.0f}", (rect.right - 106, rect.y + 28), meter_color, self.small_font)
            needs = f"H {agent.get('hunger', 0):.0f}  T {agent.get('thirst', 0):.0f}  F {agent.get('fatigue', 0):.0f}"
            self.label(needs, (rect.right - 106, rect.y + 46), MUTED, self.small_font)
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
        self.renderer = Renderer(self.screen, self.camera, seed)
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
