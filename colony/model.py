"""
model.py

Canonical Habryn colony model.

Acts as the central orchestrator for the simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from copy import deepcopy
import importlib
import re
from enum import Enum
from types import MappingProxyType
from typing import Any
from collections import deque
from math import dist
from heapq import heappop, heappush
from uuid import uuid4

from colony.environment.mars_map import MarsMap
from colony.buildings.base_building import BaseBuilding
from colony.buildings.storage_facility import StorageFacility
from colony.agents.identity import initialize_character
from colony.systems.social_manager import SocialManager
from colony.environment.day_night_cycle import DayNightCycle
from colony.environment.weather import WeatherSystem
from colony.resources.base_resource import BaseResource
from colony.tasks.task import TaskStatus, TaskPriority
from colony.systems.construction_manager import ConstructionProject
from colony.systems.logistics_manager import TransportRequest
from colony.systems.maintenance_manager import MaintenanceRequest
from colony.systems.research_manager import ResearchProject
from colony.systems.emergency_manager import Emergency, EmergencySeverity
from colony.scheduler import Scheduler
from colony.events.event_manager import EventManager
from colony.events.base_event import BaseEvent, EventSeverity
from colony.events.accidents import Accident
from colony.events.failures import Failure
from colony.events.random_events import RandomEvent
from colony.events.accidents import AccidentManager
from colony.events.failures import FailureManager
from colony.events.random_events import RandomEventManager
from colony.systems.ai_manager import AIManager
from colony.systems.autonomy_manager import AutonomyManager
from colony.systems.construction_manager import ConstructionManager
from colony.systems.economy_manager import EconomyManager
from colony.systems.emergency_manager import EmergencyManager
from colony.systems.logistics_manager import LogisticsManager
from colony.systems.maintenance_manager import MaintenanceManager
from colony.systems.population_manager import PopulationManager
from colony.systems.power_grid import PowerGrid
from colony.systems.resource_manager import ResourceManager
from colony.systems.research_manager import ResearchManager
from colony.systems.task_manager import TaskManager


@dataclass(frozen=True)
class WorldSnapshot:
    """Read-only render boundary for the authoritative colony world."""
    width: int
    height: int
    tiles: tuple[tuple[int, int, str, bool, bool, tuple[tuple[str, float], ...], str], ...]
    agents: tuple[MappingProxyType, ...]
    buildings: tuple[MappingProxyType, ...]
    tick: int
    time: str
    telemetry: MappingProxyType

# ============================================================
# Colony Model
# ============================================================


@dataclass
class ColonyModel:

    scheduler: Scheduler

    mars_map: MarsMap = field(default_factory=MarsMap)
    world_seed: int = 42
    needs_intensity: float = 1.0
    radiation_severity: float = 1.0
    colony_name: str = "Habryn"
    colony_id: str = "COLONY-07"
    arrival_schedule: tuple[tuple[int, int, int], ...] = ()
    processed_arrivals: set[int] = field(default_factory=set)
    discovered_deposits: list[dict[str, Any]] = field(default_factory=list)
    exploration_reports: list[dict[str, Any]] = field(default_factory=list)
    agents_by_id: dict[Any, Any] = field(default_factory=dict)
    buildings_by_id: dict[Any, Any] = field(default_factory=dict)
    weather: WeatherSystem = field(default_factory=WeatherSystem)
    day_night: DayNightCycle = field(default_factory=DayNightCycle)
    _restoring_entities: bool = field(default=False, repr=False)
    _habitat_entries_cache: tuple[tuple[int, int], ...] | None = field(default=None, repr=False)
    _facility_entries_cache: dict[str, tuple[tuple[int, int], ...]] = field(default_factory=dict, repr=False)

    event_manager: EventManager = field(
        default_factory=EventManager,
    )

    accident_manager: AccidentManager = field(
        default_factory=AccidentManager,
    )

    failure_manager: FailureManager = field(
        default_factory=FailureManager,
    )

    random_event_manager: RandomEventManager = field(
        default_factory=RandomEventManager,
    )

    power_grid: PowerGrid = field(
        default_factory=PowerGrid,
    )

    resource_manager: ResourceManager = field(
        default_factory=ResourceManager,
    )

    population_manager: PopulationManager = field(
        default_factory=PopulationManager,
    )

    construction_manager: ConstructionManager = field(
        default_factory=ConstructionManager,
    )

    logistics_manager: LogisticsManager = field(
        default_factory=LogisticsManager,
    )

    research_manager: ResearchManager = field(
        default_factory=ResearchManager,
    )

    economy_manager: EconomyManager = field(
        default_factory=EconomyManager,
    )

    emergency_manager: EmergencyManager = field(
        default_factory=EmergencyManager,
    )

    maintenance_manager: MaintenanceManager = field(
        default_factory=MaintenanceManager,
    )

    ai_manager: AIManager = field(
        default_factory=AIManager,
    )

    autonomy_manager: AutonomyManager = field(default_factory=AutonomyManager)

    social_manager: SocialManager = field(default_factory=SocialManager)

    task_manager: TaskManager = field(
        default_factory=TaskManager,
    )

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        if self.scheduler is None:

            raise ValueError(
                "ColonyModel requires a Scheduler.",
            )

        self.connect_managers()

        self.initialize_managers()

    # ========================================================
    # Manager Connections
    # ========================================================

    def connect_managers(
        self,
    ) -> None:

        # Construction

        self.construction_manager.connect_resource_manager(
            self.resource_manager,
        )

        self.construction_manager.connect_power_grid(
            self.power_grid,
        )

        self.construction_manager.connect_population_manager(
            self.population_manager,
        )

        # ========================================================
        # Scheduler
        # ========================================================

        for manager in self.managers:

            manager.scheduler = self.scheduler

        # ========================================================
        # Event System
        # ========================================================

        self.accident_manager.connect_event_manager(
            self.event_manager,
        )

        self.accident_manager.connect_emergency_manager(
            self.emergency_manager,
        )

        self.failure_manager.connect_event_manager(
            self.event_manager,
        )

        self.failure_manager.connect_emergency_manager(
            self.emergency_manager,
        )

        self.random_event_manager.connect_event_manager(
            self.event_manager,
        )

    # ========================================================
    # Manager Initialization
    # ========================================================

    def initialize_managers(
        self,
    ) -> None:

        managers = (
            self.event_manager,
            self.accident_manager,
            self.failure_manager,
            self.random_event_manager,
            self.power_grid,
            self.resource_manager,
            self.population_manager,
            self.construction_manager,
            self.logistics_manager,
            self.research_manager,
            self.economy_manager,
            self.emergency_manager,
            self.maintenance_manager,
            self.ai_manager,
            self.autonomy_manager,
            self.social_manager,
            self.task_manager,
        )

        for manager in managers:

            manager.initialize()

    # ========================================================
    # Manager Collection
    # ========================================================

    @property
    def managers(
        self,
    ) -> tuple:

        return (
            self.event_manager,
            self.accident_manager,
            self.failure_manager,
            self.random_event_manager,
            self.power_grid,
            self.resource_manager,
            self.population_manager,
            self.construction_manager,
            self.logistics_manager,
            self.research_manager,
            self.economy_manager,
            self.emergency_manager,
            self.maintenance_manager,
            self.ai_manager,
            self.autonomy_manager,
            self.social_manager,
            self.task_manager,
        )

    # ========================================================
    # Simulation
    # ========================================================

    def step(
        self,
    ) -> None:

        self.step_core()

        self.step_agents_and_tasks()

        self.step_resources()

        self.step_population()

        self.step_colony()

        self.step_events()

        self.process_scheduler_events()

    def register_agent(self, agent: Any) -> None:
        key = getattr(agent, "unique_id", id(agent))
        if key in self.agents_by_id:
            raise ValueError(f"Agent {key!r} is already registered")
        initialize_character(agent, self.world_seed)
        position = tuple(agent.position)
        if not self.mars_map.in_bounds(*position):
            raise ValueError(f"Agent position {position} is outside the map")
        tile = self.mars_map.get_tile(*position)
        if tile is None or not tile.walkable or tile.building is not None:
            raise ValueError(f"Agent position {position} is not walkable")
        if not self.mars_map.add_agent(agent, position):
            raise ValueError(f"Could not place agent at {position}")
        self.agents_by_id[key] = agent
        self.ai_manager.register_agent(agent)
        if hasattr(agent, "suit_oxygen"):
            self.accident_manager.register_astronaut(agent)
        elif "robot" in type(agent).__name__.lower():
            self.accident_manager.register_robot(agent)
        if hasattr(agent, "suit_oxygen") and not self._restoring_entities:
            population = self.resource_manager.resource("Population")
            if population is not None:
                population.generate(1.0)
                self.population_manager.update_population()
        if "robot" in type(agent).__name__.lower():
            register = getattr(self.logistics_manager, "register_robot", None)
            if register:
                register(agent)

    def register_visible_deposits(self) -> None:
        """Record finite deposits already present in surveyed map cells."""
        known = {(tuple(item["position"]), item["resource"]): item for item in self.discovered_deposits}
        for position, tile in self.mars_map.tiles.items():
            if not tile.explored:
                continue
            for resource, amount in sorted(tile.resource_deposit.items()):
                if amount > 0 and (position, resource) not in known:
                    self.discovered_deposits.append({"position": list(position), "resource": resource,
                                                     "remaining": amount,
                                                     "discovered_tick": self.scheduler.tick})
                elif (position, resource) in known:
                    known[(position, resource)]["remaining"] = amount
        for (position, resource), item in known.items():
            item["remaining"] = self.mars_map.resource_amount(*position, resource)

    def reveal_area(self, center: tuple[int, int], radius: int = 2) -> int:
        """Reveal a rover survey area and record resource deposits it finds."""
        previous = len(self.mars_map.explored_tiles())
        for y in range(max(0, center[1] - radius), min(self.mars_map.height, center[1] + radius + 1)):
            for x in range(max(0, center[0] - radius), min(self.mars_map.width, center[0] + radius + 1)):
                if abs(x - center[0]) + abs(y - center[1]) <= radius:
                    self.mars_map.explore(x, y)
        self.register_visible_deposits()
        return len(self.mars_map.explored_tiles()) - previous

    def remove_agent(self, agent_or_id: Any) -> Any:
        key = getattr(agent_or_id, "unique_id", agent_or_id)
        agent = self.agents_by_id.pop(key, None)
        if agent is not None:
            self.mars_map.remove_agent(agent, tuple(agent.position))
            self.ai_manager.unregister_agent(agent)
            if hasattr(agent, "suit_oxygen"):
                self.accident_manager.unregister_astronaut(agent)
            elif "robot" in type(agent).__name__.lower():
                self.accident_manager.unregister_robot(agent)
            self.logistics_manager.robots.pop(key, None)
            if hasattr(agent, "suit_oxygen"):
                population = self.resource_manager.resource("Population")
                if population is not None:
                    population.consume(1.0)
                    self.population_manager.update_population()
        return agent

    def move_agent(self, agent_or_id: Any, destination: tuple[int, int]) -> bool:
        key = getattr(agent_or_id, "unique_id", agent_or_id)
        agent = self.agents_by_id.get(key)
        if agent is None:
            raise KeyError(f"Unknown agent {key!r}")
        source = tuple(agent.position)
        if not self.mars_map.move_agent(agent, source, destination):
            return False
        agent.position = tuple(destination)
        return True

    def place_building(self, building: Any, width: int | None = None, height: int | None = None) -> bool:
        key = getattr(building, "building_id", id(building))
        if key in self.buildings_by_id:
            raise ValueError(f"Building {key!r} is already registered")
        default_width, default_height = type(building).default_footprint
        width = default_width if width is None else width
        height = default_height if height is None else height
        if not self.mars_map.place_building(building, tuple(building.position), width, height):
            return False
        self.buildings_by_id[key] = building
        self._habitat_entries_cache = None
        self._facility_entries_cache.clear()
        self._register_building_systems(building)
        return True

    def _register_building_systems(self, building: Any) -> None:
        for attr, value in vars(building).items():
            if isinstance(value, BaseResource):
                shared = self.resource_manager.resource(value.name)
                if shared is not None:
                    setattr(building, attr, shared)
            elif attr == "fuel" and (type(building).__name__ in {"Reactor", "LaunchPad"}
                                      or isinstance(building, StorageFacility)):
                shared = self.resource_manager.resource("Fuel")
                if shared is None:
                    raise ValueError("Fuel-using buildings require the colony Fuel inventory")
                setattr(building, attr, shared)
        self.ai_manager.register_building(building)
        self.maintenance_manager.register_building(building)
        self.logistics_manager.register_building(building)
        self.failure_manager.register_building(building)
        if getattr(building, "power_required", 0.0) > 0.0:
            self.power_grid.register_consumer(building)
        if hasattr(building, "power_output"):
            self.power_grid.register_producer(building)
        if type(building).__name__ == "Battery":
            self.power_grid.register_battery(building)
        if hasattr(building, "housing_capacity"):
            self.population_manager.housing_capacity += building.housing_capacity

    def remove_building(self, building_or_id: Any) -> Any:
        key = getattr(building_or_id, "building_id", building_or_id)
        building = self.buildings_by_id.pop(key, None)
        if building is not None:
            self.mars_map.remove_building(tuple(building.position))
            self._habitat_entries_cache = None
            self._facility_entries_cache.clear()
            self.ai_manager.buildings.pop(key, None)
            self.maintenance_manager.unregister_building(building)
            self.logistics_manager.buildings.pop(key, None)
            self.failure_manager.unregister_building(building)
            self.power_grid.unregister_building(building)
            if hasattr(building, "housing_capacity"):
                self.population_manager.housing_capacity = max(
                    0, self.population_manager.housing_capacity - building.housing_capacity)
        return building

    def get_entity(self, entity_id: Any) -> Any | None:
        return self.agents_by_id.get(entity_id, self.buildings_by_id.get(entity_id))

    def world_snapshot(self) -> WorldSnapshot:
        tiles = tuple((x, y, tile.terrain.name, tile.explored, tile.occupied,
                       tuple(sorted(tile.resource_deposit.items())), tile.region)
                      for (x, y), tile in self.mars_map.tiles.items())
        agents = tuple(MappingProxyType({**a.statistics(), "id": key, "name": getattr(a, "name", type(a).__name__),
            "category": "robot" if "robot" in type(a).__name__.lower() else "agent",
            "profession": getattr(a, "profession", ""), "position": tuple(a.position),
            "health": getattr(a, "health", None), "alive": getattr(a, "alive", True),
            "recent_conversations": self.social_manager.recent_for(key),
            "relationship_list": [relationship.to_dict() for relationship in self.social_manager.relationships.values()
                                  if key in (relationship.first_id, relationship.second_id)]})
            for key, a in self.agents_by_id.items())
        buildings = tuple(MappingProxyType({**b.statistics(), "id": key, "name": getattr(b, "name", type(b).__name__),
            "category": type(b).__name__, "position": tuple(b.position),
            "footprint": (max((t.local_x for t in self.mars_map.tiles.values() if t.building is b), default=0) + 1,
                          max((t.local_y for t in self.mars_map.tiles.values() if t.building is b), default=0) + 1),
            "enabled": getattr(b, "enabled", None), "integrity": getattr(b, "integrity", None)})
            for key, b in self.buildings_by_id.items())
        telemetry = self.statistics()
        telemetry["map"] = self.mars_map.statistics()
        telemetry["resource_inventory"] = {
            name: resource.statistics() for name, resource in self.resource_manager.resources.items()
        }
        fuel_resource = self.resource_manager.resource("Fuel")
        fuel_tasks = [task for task in self.task_manager.tasks
                      if task.metadata.get("action") == "fuel_harvest"
                      and task.status not in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}]
        telemetry["fuel_logistics"] = {
            "deposit_amount": sum(tile.resource_deposit.get("Fuel", 0.0)
                                  for tile in self.mars_map.tiles.values()),
            "in_transit": sum(item.quantity for agent in self.agents_by_id.values()
                               for name, item in agent.inventory.items() if name == "Fuel"),
            "consumed_total": float(getattr(fuel_resource, "total_consumed", 0.0)),
            "active_tasks": [{"name": task.name, "phase": task.metadata.get("phase", "extract"),
                              "progress": task.progress,
                              "worker": getattr(task.assigned_agent, "name", None)}
                             for task in fuel_tasks],
        }
        telemetry["exploration_reports"] = [dict(report) for report in self.exploration_reports[-12:]]
        telemetry["known_deposits"] = [dict(deposit) for deposit in self.discovered_deposits]
        telemetry["logistics_requests"] = [
            {"id": item.request_id, "resource": item.resource, "amount": item.amount,
             "source": item.source if isinstance(item.source, str) else self._entity_reference(item.source),
             "destination": getattr(item.destination, "name", str(item.destination)),
             "carrier": getattr(item.assigned_robot, "name", None),
             "loading_progress": item.loading_progress, "travel_progress": item.travel_progress,
             "unloading_progress": item.unloading_progress,
             "status": "completed" if item.completed else "failed" if item.failed else "in transit"
             if item.assigned_robot is not None else "awaiting assignment"}
            for item in list(self.logistics_manager.delivery_queue)[-20:]
        ]
        telemetry["events_feed"] = [event.statistics() for event in self.event_manager.active_events]
        telemetry["social"] = self.social_manager.statistics()
        telemetry["conversations"] = [item.to_dict() for item in self.social_manager.conversations[-12:]]
        telemetry["active_conversations"] = [item.to_dict() for item in self.social_manager.conversations
                                              if item.active]
        telemetry["warnings"] = sorted(self.resource_manager.shortages)
        telemetry["ai_goals"] = [dict(goal) for goal in self.ai_manager.goals]
        telemetry["ai_decisions"] = [dict(decision) for decision in self.ai_manager.decisions[-12:]]
        telemetry["resource_forecasts"] = {
            name: dict(forecast) for name, forecast in self.ai_manager.resource_forecasts.items()
        }
        telemetry["construction_projects"] = [
            {"name": project.building_name, "position": project.position, "progress": project.progress,
             "status": "Active" if project in self.construction_manager.active_projects else "Queued",
             "worker": getattr(project.assigned_agent, "name", None)}
            for project in (*self.construction_manager.active_projects, *self.construction_manager.construction_queue)
        ]
        telemetry["research_projects"] = [
            {"name": project.name, "progress": project.progress, "required_points": project.required_points,
             "status": "Complete" if project.completed else "Active" if project in self.research_manager.active_projects else "Queued",
             "scientist": getattr(project.assigned_scientist, "name", None)}
            for project in (*self.research_manager.active_projects, *self.research_manager.research_queue,
                            *self.research_manager.completed_projects)
        ]
        telemetry["weather"] = self.weather.statistics()
        telemetry["day_night"] = self.day_night.statistics()
        stats = MappingProxyType(telemetry)
        return WorldSnapshot(self.mars_map.width, self.mars_map.height, tiles, agents, buildings,
            self.scheduler.tick, f"Sol {self.scheduler.sol} · {self.scheduler.hour:02}:00", stats)

    # ========================================================
    # Simulation Phases
    # ========================================================

    def _path_for(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
        if start == goal:
            return []
        frontier = []
        heappush(frontier, (0.0, 0.0, start))
        parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        cost_so_far = {start: 0.0}
        while frontier:
            _priority, cost, position = heappop(frontier)
            if position == goal:
                path = []
                cursor = goal
                while cursor != start:
                    path.append(cursor)
                    cursor = parent[cursor]
                return list(reversed(path))
            if cost > cost_so_far.get(position, float("inf")):
                continue
            for tile in self.mars_map.walkable_neighbors(*position):
                next_position = (tile.x, tile.y)
                step_cost = max(0.1, float(tile.terrain.movement_cost))
                next_cost = cost + step_cost
                if next_cost >= cost_so_far.get(next_position, float("inf")):
                    continue
                cost_so_far[next_position] = next_cost
                parent[next_position] = position
                heuristic = abs(goal[0] - tile.x) + abs(goal[1] - tile.y)
                heappush(frontier, (next_cost + heuristic, next_cost, next_position))
        return []

    def move_agent_to(self, agent_or_id: Any, destination: tuple[int, int]) -> bool:
        key = getattr(agent_or_id, "unique_id", agent_or_id)
        agent = self.agents_by_id.get(key)
        if agent is None:
            raise KeyError(f"Unknown agent {key!r}")
        if not self.mars_map.in_bounds(*destination):
            return False
        path = self._path_for(tuple(agent.position), tuple(destination))
        if tuple(agent.position) != tuple(destination) and not path:
            return False
        agent.destination = tuple(destination)
        agent.path = path
        agent.moving = bool(path)
        return True

    def queue_construction(self, building_name: str, position: tuple[int, int],
                           required_resources: dict[str, float] | None = None,
                           priority: int = 2) -> ConstructionProject:
        """Validate a site and queue a real building project through the manager."""
        if not building_name or building_name == "BaseBuilding":
            raise ValueError("Select a concrete building type")
        module_name = re.sub(r"(?<!^)(?=[A-Z])", "_", building_name).lower()
        if not module_name.replace("_", "").isalnum():
            raise ValueError("Invalid building type")
        module = importlib.import_module(f"colony.buildings.{module_name}")
        building_class = getattr(module, building_name, None)
        if building_class is None or not isinstance(building_class, type) or not issubclass(building_class, BaseBuilding):
            raise ValueError(f"Unknown building type: {building_name}")
        footprint = building_class.default_footprint
        x, y = tuple(position)
        footprint_tiles = []
        for dy in range(footprint[1]):
            for dx in range(footprint[0]):
                tile = self.mars_map.get_tile(x + dx, y + dy)
                if tile is None or not tile.terrain.buildable or tile.occupied or tile.agents:
                    raise ValueError("The selected construction footprint is unavailable")
                footprint_tiles.append((x + dx, y + dy))
        projects = list(self.construction_manager.construction_queue) + list(self.construction_manager.active_projects)
        for project in projects:
            other_module = importlib.import_module(
                f"colony.buildings.{re.sub(r'(?<!^)(?=[A-Z])', '_', project.building_name).lower()}"
            )
            other_class = getattr(other_module, project.building_name)
            other_size = project.footprint or other_class.default_footprint
            ox, oy = project.position
            if any(ox <= tx < ox + other_size[0] and oy <= ty < oy + other_size[1]
                   for tx, ty in footprint_tiles):
                raise ValueError("A queued project already reserves part of that footprint")
        costs = dict(required_resources or {"Minerals": 60.0})
        if any(amount < 0 for amount in costs.values()):
            raise ValueError("Construction costs cannot be negative")
        if any(self.resource_manager.amount(name) < amount for name, amount in costs.items()):
            raise ValueError("The colony does not have the required construction resources")
        project = self.construction_manager.create_project(building_name, (x, y), costs, priority)
        project.footprint = footprint
        return project

    def create_fuel_harvest_task(self, deposit_position: tuple[int, int], amount: float,
                                 storage_building: Any | None = None):
        """Create a real mine, carry and deliver task against finite map fuel."""
        tile = self.mars_map.get_tile(*deposit_position)
        fuel = self.resource_manager.resource("Fuel")
        tasks = tuple(self.task_manager.tasks)
        reserved_at_site = sum(float(task.metadata.get("amount", 0.0))
                               for task in tasks if task.metadata.get("action") == "fuel_harvest"
                               and task.metadata.get("phase") == "extract"
                               and tuple(task.metadata.get("deposit", ())) == tuple(deposit_position))
        reserved_capacity = sum(float(task.metadata.get("amount", 0.0))
                                for task in tasks if task.metadata.get("action") == "fuel_harvest")
        if (tile is None or amount <= 0
                or tile.resource_deposit.get("Fuel", 0.0) - reserved_at_site < amount):
            raise ValueError("The selected finite fuel deposit cannot supply that amount")
        if fuel is None or fuel.storage_capacity - fuel.current_amount - reserved_capacity < amount:
            raise ValueError("Colony fuel storage cannot accept that amount")
        if storage_building is None:
            storage_building = next((item for item in self.buildings_by_id.values()
                                     if type(item).__name__ == "FuelDepot"), None)
        if storage_building is None:
            storage_building = next((item for item in self.buildings_by_id.values()
                                     if isinstance(item, StorageFacility)
                                     and item.accepts_resource("Fuel")), None)
        if (storage_building is None or storage_building.building_id not in self.buildings_by_id
                or not storage_building.operational):
            raise ValueError("Fuel delivery requires a registered, operational Fuel Depot")
        if not storage_building.accepts_resource("Fuel"):
            raise ValueError("The selected storage facility does not accept Fuel")
        maximum_stock = storage_building.maximum_stock or fuel.storage_capacity
        if fuel.current_amount + reserved_capacity + amount > maximum_stock:
            raise ValueError("The Fuel Depot's maximum stock would be exceeded")
        delivery_entry = self._building_entry(storage_building, tuple(deposit_position))
        if (not tile.walkable or delivery_entry is None
                or not self._path_for(tuple(deposit_position), delivery_entry)):
            raise ValueError("The mapped deposit has no walkable route to colony storage")
        task = self.task_manager.create_task(
            name="Harvest and deliver fuel",
            description=f"Extract {amount:g} L from the mapped deposit and carry it to colony storage.",
            priority=TaskPriority.HIGH, duration=1)
        task.task_id = f"fuel-harvest-{self.scheduler.tick}-{deposit_position[0]}-{deposit_position[1]}"
        task.target = storage_building
        task.location = tuple(deposit_position)
        task.required_skills = {"engineering": 1}
        request = self.logistics_manager.create_request(
            "Fuel", float(amount), f"MarsMap deposit {deposit_position}", storage_building,
            priority=5)
        request.request_id = f"transport-{task.task_id}"
        task.metadata = {"action": "fuel_harvest", "phase": "extract",
                         "amount": float(amount), "deposit": list(deposit_position),
                         "storage_building_id": storage_building.building_id,
                         "logistics_request_id": request.request_id}
        return task

    def step_agents_and_tasks(self) -> None:
        self._assign_emergency_tasks()
        self._assign_rover_recovery_tasks()
        self._assign_construction_projects()
        pending = self.task_manager.pending_tasks()
        hour = self.scheduler.hour
        colony_emergency = bool(self.emergency_manager.active_emergencies)
        for agent in self.agents_by_id.values():
            if not getattr(agent, "alive", True):
                if hasattr(agent, "suit_oxygen") and not agent.metadata.get("population_removed", False):
                    population = self.resource_manager.resource("Population")
                    if population is not None:
                        population.consume(1.0)
                    self.population_manager.update_population()
                    self.population_manager.update_housing()
                    agent.metadata["population_removed"] = True
                agent.current_activity = "Dead"
                continue
            if hasattr(agent, "battery_level") and agent.battery_level <= 0.0:
                if agent.current_task is not None:
                    stranded_task = agent.current_task
                    self.task_manager.unassign_task(agent)
                    if stranded_task not in pending:
                        pending.append(stranded_task)
                agent.current_activity = "Stranded — battery depleted"
                agent.decision_reason = "The rover is offline and requires a recovery or charging crew."
                agent.moving = False
                agent.path.clear()
                continue
            if not self.autonomy_manager.enabled and not getattr(agent, "busy", False):
                agent.current_activity = "Autonomy disabled"
                agent.decision_reason = "Autonomous task and activity selection is disabled in colony settings."
                self._advance_agent_movement(agent)
                continue
            research_project = next((project for project in self.research_manager.active_projects
                                     if project.assigned_scientist is agent and not project.completed), None)
            if research_project is not None and getattr(agent, "assigned_laboratory", None) is not None:
                entry = self._nearest_facility_entry(agent, "laboratory")
                if entry is not None and tuple(agent.position) != entry:
                    if not agent.moving:
                        self.move_agent_to(agent, entry)
                    agent.current_activity = "Walking to Laboratory"
                    agent.decision_reason = f"Assigned to research project: {research_project.name}."
                else:
                    agent.current_activity = "Operating Equipment"
                    agent.state = type(agent.state).RESEARCHING
                    agent.decision_reason = f"Conducting {research_project.name} at an operational laboratory."
                self._advance_agent_movement(agent)
                continue
            conversation = self.social_manager.active_for(agent.unique_id, self.scheduler.tick)
            if conversation and agent.current_task is None:
                agent.current_activity = "Socializing"
                agent.state = type(agent.state).SOCIALIZING
                continue
            if (not getattr(agent, "busy", False)
                    and agent.current_activity in {"Eating", "Drinking", "Recreation"}
                    and self.scheduler.tick < agent.activity_until_tick):
                continue
            critical_work = any(getattr(task.priority, "value", 0) >= 5 for task in pending)
            decision = self.autonomy_manager.decide(agent, hour, colony_emergency or critical_work)
            agent.next_activity = decision.next_activity
            agent.decision_reason = decision.reason
            if getattr(agent, "busy", False) and (
                decision.action == "emergency"
                or (decision.action == "recharge" and getattr(agent, "battery_level", 100) <= 10)
            ):
                active_task = agent.current_task
                if active_task is not None and getattr(active_task.priority, "value", 0) < 5:
                    self.task_manager.unassign_task(agent)
                    pending.append(active_task)
                    agent.employment_status = "Available"
            if not getattr(agent, "busy", False):
                if decision.action not in {"work"}:
                    self._apply_autonomous_activity(agent, decision.action)
                    self._advance_agent_movement(agent)
                    continue
                task, reason = self.autonomy_manager.select_task(agent, pending, self, hour)
                if task is not None:
                    agent.decision_reason = reason
                if task is not None and self.task_manager.assign_task(agent, task):
                    pending.remove(task)
                    agent.employment_status = "Employed"
                    task_action = task.metadata.get("action", "")
                    agent.current_activity = {
                        "repair": "Repairing", "build": "Building", "research": "Operating Equipment",
                        "operate": "Operating Equipment", "emergency": "Emergency Response",
                    }.get(task_action, "Working")
                    for resource, amount in task.required_resources.items():
                        self.resource_manager.consume(resource, amount)
                    if task.metadata.get("action") == "maintenance":
                        request = next((item for item in self.maintenance_manager.pending_requests()
                                        if item.building is task.target and item.assigned_agent is None), None)
                        if request is not None:
                            self.maintenance_manager.assign_request(agent, request)
                    if task.location is not None:
                        self.move_agent_to(agent, task.location)
                else:
                    agent.current_activity = "Available for work" if decision.action == "work" else decision.action.title()
                    if agent.state.value not in {"Sleeping", "Eating", "Drinking"}:
                        agent.state = type(agent.state).IDLE
            self._advance_agent_movement(agent)
            task = agent.current_task
            if task is not None and task.location is not None and tuple(agent.position) != tuple(task.location):
                agent.current_activity = "Walking to Construction Site" if task.metadata.get("construction_project") else "Walking to Task"
                agent.state = type(agent.state).WALKING
                if not agent.moving:
                    self.move_agent_to(agent, tuple(task.location))
                continue
            if task is not None and agent.can_work and not agent.moving:
                if task.metadata.get("construction_project"):
                    agent.current_activity = "Building"
                    agent.state = type(agent.state).BUILDING
                if task.metadata.get("action") == "medical" and hasattr(agent, "heal_patient"):
                    agent.current_patient = task.target
                    agent.heal_patient()
                    if getattr(task.target, "radiation", 0) > 0 and hasattr(agent, "treat_radiation"):
                        agent.treat_radiation(task.target)
                elif task.metadata.get("action") == "robotics" and task.target is not None:
                    task.target.maintenance(1.0)
                if task.status != TaskStatus.IN_PROGRESS:
                    task.start()
                task.advance(100.0 / max(1, task.duration))
                project = next((item for item in self.construction_manager.active_projects
                                if item.task_id == task.task_id), None)
                if project is not None:
                    project.progress = task.progress
                if task.status == TaskStatus.COMPLETED:
                    action = task.metadata.get("action")
                    if action == "fuel_harvest" and task.metadata.get("phase") == "extract":
                        amount = float(task.metadata["amount"])
                        deposit = tuple(task.metadata["deposit"])
                        storage = self.buildings_by_id.get(task.metadata["storage_building_id"])
                        tile = self.mars_map.get_tile(*deposit)
                        available = tile.resource_deposit.get("Fuel", 0.0) if tile is not None else 0.0
                        loaded = available >= amount and agent.add_item("Fuel", amount, weight=1.0)
                        extracted = loaded and self.mars_map.remove_resource(*deposit, "Fuel", amount) >= amount
                        if extracted:
                            self.register_visible_deposits()
                        if not loaded or not extracted or storage is None:
                            if loaded:
                                agent.remove_item("Fuel", amount)
                            self.task_manager.fail_task(agent)
                            request = next((item for item in self.logistics_manager.delivery_queue
                                            if item.request_id == task.metadata.get("logistics_request_id")), None)
                            if request is not None:
                                self.logistics_manager.fail_request(request)
                            agent.current_activity = "Fuel harvest blocked"
                            agent.decision_reason = "Cargo, deposit, or storage became unavailable before extraction."
                            agent.employment_status = "Available"
                            continue
                        task.metadata["phase"] = "deliver"
                        task.metadata["loaded_amount"] = amount
                        task.metadata["loaded_tick"] = self.scheduler.tick
                        task.metadata["source"] = {"type": "MarsMap deposit", "resource": "Fuel",
                                                    "position": list(deposit)}
                        task.metadata["destination"] = {"type": type(storage).__name__,
                                                         "building_id": storage.building_id}
                        request = next((item for item in self.logistics_manager.delivery_queue
                                        if item.request_id == task.metadata.get("logistics_request_id")), None)
                        if request is None:
                            raise RuntimeError("Fuel task lost its reserved logistics request")
                        request.assigned_robot = agent
                        request.loading_progress = 100.0
                        task.progress = 0.0
                        task.status = TaskStatus.IN_PROGRESS
                        task.location = self._building_entry(storage, tuple(agent.position))
                        if task.location is None:
                            self.mars_map.add_resource(*deposit, "Fuel", amount)
                            agent.remove_item("Fuel", amount)
                            request = next((item for item in self.logistics_manager.delivery_queue
                                            if item.request_id == task.metadata.get("logistics_request_id")), None)
                            if request is not None:
                                self.logistics_manager.fail_request(request)
                            self.task_manager.fail_task(agent)
                            continue
                        agent.current_activity = "Transporting Fuel"
                        agent.decision_reason = f"Carrying {amount:g} L of extracted fuel to colony storage."
                        self.move_agent_to(agent, task.location)
                        task.metadata["delivery_route_length"] = len(agent.path)
                        continue
                    if action == "fuel_harvest" and task.metadata.get("phase") == "deliver":
                        amount = float(task.metadata["amount"])
                        fuel = self.resource_manager.resource("Fuel")
                        storage = self.buildings_by_id.get(task.metadata["storage_building_id"])
                        if (fuel is None or storage is None or not storage.operational
                                or not storage.accepts_resource("Fuel") or storage.fuel is not fuel
                                or not agent.has_item("Fuel", amount)):
                            request = next((item for item in self.logistics_manager.delivery_queue
                                            if item.request_id == task.metadata.get("logistics_request_id")), None)
                            if request is not None:
                                self.logistics_manager.fail_request(request)
                            self.task_manager.fail_task(agent)
                            agent.employment_status = "Available"
                            continue
                        before = fuel.current_amount
                        if not self.resource_manager.produce("Fuel", amount):
                            request = next((item for item in self.logistics_manager.delivery_queue
                                            if item.request_id == task.metadata.get("logistics_request_id")), None)
                            if request is not None:
                                self.logistics_manager.fail_request(request)
                            self.task_manager.fail_task(agent)
                            agent.employment_status = "Available"
                            continue
                        accepted = fuel.current_amount - before
                        if accepted != amount:
                            # create_fuel_harvest_task reserves capacity up front; this
                            # guard prevents cargo disappearing if state changed meanwhile.
                            fuel.consume(accepted)
                            self.resource_manager.production_history["Fuel"] -= accepted
                            self.task_manager.fail_task(agent)
                            request = next((item for item in self.logistics_manager.delivery_queue
                                            if item.request_id == task.metadata.get("logistics_request_id")), None)
                            if request is not None:
                                self.logistics_manager.fail_request(request)
                            agent.employment_status = "Available"
                            continue
                        agent.remove_item("Fuel", amount)
                        storage.total_resources_transferred += amount
                        self.resource_manager.transfer("Fuel", amount)
                        request = next((item for item in self.logistics_manager.delivery_queue
                                        if item.request_id == task.metadata.get("logistics_request_id")), None)
                        if request is None:
                            raise RuntimeError("Delivered Fuel has no logistics manifest")
                        request.unloading_progress = 100.0
                        self.logistics_manager.complete_request(request)
                        task.metadata["delivered_amount"] = accepted
                        task.metadata["delivered_tick"] = self.scheduler.tick
                        task.metadata["transfer_event"] = {
                            "resource": "Fuel", "quantity": accepted,
                            "source": dict(task.metadata["source"]),
                            "destination": dict(task.metadata["destination"]),
                            "completed_tick": self.scheduler.tick,
                        }
                    if action == "explore":
                        revealed = self.reveal_area(tuple(task.location), int(task.metadata.get("radius", 2)))
                        if hasattr(agent, "consume_battery"):
                            agent.consume_battery(float(task.metadata.get("work_energy", 2.0)))
                            agent.durability = max(0.0, agent.durability - .05)
                        report = {"tick": self.scheduler.tick, "rover_id": agent.unique_id,
                                  "rover": agent.name, "position": list(task.location),
                                  "tiles_revealed": revealed,
                                  "deposits": [dict(item) for item in self.discovered_deposits
                                               if abs(item["position"][0] - task.location[0])
                                               + abs(item["position"][1] - task.location[1])
                                               <= int(task.metadata.get("radius", 2))]}
                        self.exploration_reports.append(report)
                        self.exploration_reports[:] = self.exploration_reports[-500:]
                    if action == "recover_rover":
                        rover = task.target
                        recovery_cost = float(task.metadata.get("power_cost", 10.0))
                        if (rover is None or getattr(rover, "battery_level", 1.0) > 0.0
                                or not self.resource_manager.consume("Power", recovery_cost)):
                            self.task_manager.fail_task(agent)
                            agent.current_activity = "Rover recovery blocked"
                            agent.decision_reason = "A stranded rover needs a reachable engineer and ten units of power."
                            agent.employment_status = "Available"
                            continue
                        rover.recharge(float(task.metadata.get("charge_amount", 25.0)))
                        if rover.battery_level < 20.0:
                            self.task_manager.fail_task(agent)
                            agent.employment_status = "Available"
                            continue
                        task.metadata["recovered_tick"] = self.scheduler.tick
                        task.metadata["power_consumed"] = recovery_cost
                    if action == "farm_water":
                        water_cost = float(task.metadata.get("water_cost", 2.0))
                        farmer = hasattr(agent, "water") and hasattr(agent, "assign_greenhouse")
                        watered = (farmer and task.target is not None
                                   and self.resource_manager.consume("Water", water_cost))
                        if watered:
                            agent.assign_greenhouse(task.target)
                            watered = agent.water()
                        if not watered:
                            self.task_manager.fail_task(agent)
                            agent.current_activity = "Work blocked"
                            agent.decision_reason = "Greenhouse care could not complete: farmer, target, or water unavailable."
                            agent.employment_status = "Available"
                            continue
                    elif action == "maintenance" and task.target is not None:
                        if hasattr(agent, "maintain"):
                            agent.maintain(task.target)
                        request = next((item for item in self.maintenance_manager.maintenance_queue
                                        if item.building is task.target and item.assigned_agent is agent), None)
                        if request is not None:
                            self.maintenance_manager.complete_request(request)
                            self.maintenance_manager.maintenance_queue.remove(request)
                    if project is not None:
                        if not self._complete_construction(project, agent):
                            for name, amount in project.required_resources.items():
                                resource = self.resource_manager.resource(name)
                                if resource is not None:
                                    resource.generate(amount)
                            self.construction_manager.cancel_project(project)
                            self.task_manager.fail_task(agent)
                            agent.employment_status = "Available"
                            continue
                    if task.metadata.get("action") == "repair" and task.target is not None:
                        task.target.repair(float(task.metadata.get("repair_amount", 10.0)))
                        task.target.emergency_shutdown = False
                        task.target.set_power(True)
                    self._resolve_agent_emergency(agent, task.target)
                    self.task_manager.complete_task(agent)
                    self._award_task_experience(agent, task)
                    agent.employment_status = "Available"

    def _assign_construction_projects(self) -> None:
        if not self.autonomy_manager.enabled:
            return
        for project in sorted(tuple(self.construction_manager.construction_queue),
                              key=lambda item: -item.priority):
            agent = next((item for item in self.agents_by_id.values()
                          if hasattr(item, "suit_oxygen") and item.alive and not item.busy
                          and item.current_task is None
                          and item.skill_levels.get("construction", 0) >= 1), None)
            if agent is None:
                return
            if not self.construction_manager.assign_project(agent, project):
                continue
            entry = self._construction_entry(project, agent)
            if entry is None:
                self.construction_manager.cancel_project(project)
                for name, amount in project.required_resources.items():
                    resource = self.resource_manager.resource(name)
                    if resource is not None:
                        resource.generate(amount)
                continue
            task = self.task_manager.create_task(
                name=f"Construct {project.building_name}",
                description=f"Build at {project.position}; required skills: construction.",
                priority=TaskPriority(max(1, min(5, project.priority))), duration=20)
            task.task_id = (f"construction-{self.scheduler.tick}-{project.building_name}-"
                            f"{project.position[0]}-{project.position[1]}")
            task.location = entry
            task.required_skills = {"construction": 1}
            task.metadata.update({"action": "build", "construction_project": True})
            project.task_id = task.task_id
            if not self.task_manager.assign_task(agent, task):
                self.construction_manager.cancel_project(project)
                for name, amount in project.required_resources.items():
                    resource = self.resource_manager.resource(name)
                    if resource is not None:
                        resource.generate(amount)
            else:
                agent.employment_status = "Employed"
                agent.current_activity = "Building"
                agent.decision_reason = f"Assigned construction project at {project.position}."

    def _assign_emergency_tasks(self) -> None:
        for emergency in sorted(tuple(self.emergency_manager.emergency_queue),
                                key=lambda item: -item.severity.value):
            target = emergency.target
            is_building = hasattr(target, "building_id")
            candidates = [agent for agent in self.agents_by_id.values()
                          if hasattr(agent, "suit_oxygen") and agent.alive and not agent.busy
                          and agent.current_task is None]
            if is_building:
                responders = [agent for agent in candidates
                              if agent.profession == "Engineer" or agent.skill_levels.get("engineering", 0) >= 1]
                action = "repair"
                location = self._building_entry(target)
            elif target is not None and "robot" not in type(target).__name__.lower():
                responders = [agent for agent in candidates if agent.profession == "Medic"]
                action = "medical"
                location = tuple(target.position)
            else:
                responders = [agent for agent in candidates
                              if agent.profession == "Engineer" or agent.skill_levels.get("engineering", 0) >= 1]
                action = "robotics"
                location = tuple(target.position) if target is not None else emergency.location
            if not responders or location is None:
                continue
            responder = min(responders, key=lambda agent: (agent.distance_to(location), agent.unique_id))
            active = self.emergency_manager.next_emergency()
            if active is not emergency:
                continue
            if not self.emergency_manager.assign_emergency(responder, emergency):
                self.emergency_manager.emergency_queue.appendleft(emergency)
                self.emergency_manager.active_emergencies.remove(emergency)
                continue
            priority = TaskPriority(min(5, max(4, emergency.severity.value + 1)))
            task = self.task_manager.create_task(
                name=f"Respond: {emergency.title}", description=emergency.description,
                priority=priority, duration=12)
            task.target = target
            task.location = tuple(location)
            task.metadata.update({"action": action, "emergency_response": True,
                                  "repair_amount": max(20.0, float(emergency.severity.value) * 25)})
            if self.task_manager.assign_task(responder, task):
                responder.employment_status = "Emergency Response"
                responder.current_activity = "Emergency Response"
                responder.decision_reason = emergency.description
                if action == "medical" and hasattr(responder, "current_patient"):
                    responder.current_patient = target

    def _assign_rover_recovery_tasks(self) -> None:
        """Send an engineer with finite colony power to physically restart a rover."""
        existing = {(task.metadata.get("rover_id")) for task in self.task_manager.tasks
                    if task.metadata.get("action") == "recover_rover"}
        for rover in self.agents_by_id.values():
            if not hasattr(rover, "battery_level") or rover.battery_level > 0 or rover.unique_id in existing:
                continue
            responders = [agent for agent in self.agents_by_id.values()
                          if hasattr(agent, "suit_oxygen") and agent.alive and not agent.busy
                          and agent.skill_levels.get("engineering", 0) >= 1]
            candidates = []
            for neighbor in self.mars_map.neighbors(*rover.position):
                if not neighbor.walkable:
                    continue
                for engineer in responders:
                    path = self._path_for(tuple(engineer.position), (neighbor.x, neighbor.y))
                    if path or tuple(engineer.position) == (neighbor.x, neighbor.y):
                        candidates.append((len(path), engineer.unique_id, (neighbor.x, neighbor.y)))
            if not candidates:
                continue
            _distance, _engineer_id, location = min(candidates)
            task = self.task_manager.create_task(
                name=f"Recover {rover.name}",
                description="Travel to the stranded rover and consume colony power to restart it.",
                priority=TaskPriority.CRITICAL, duration=2)
            task.target = rover
            task.location = location
            task.required_skills = {"engineering": 1}
            task.metadata = {"action": "recover_rover", "rover_id": rover.unique_id,
                             "power_cost": 10.0, "charge_amount": 25.0}
            existing.add(rover.unique_id)

    def _building_entry(self, building: Any, from_position: tuple[int, int] | None = None) -> tuple[int, int] | None:
        candidates = set()
        for tile in self.mars_map.tiles.values():
            if tile.building is building:
                candidates.update((neighbor.x, neighbor.y)
                                  for neighbor in self.mars_map.walkable_neighbors(tile.x, tile.y))
        origin = tuple(from_position or building.position)
        return min(candidates, key=lambda point: (abs(point[0] - origin[0])
                                                   + abs(point[1] - origin[1]), point[1], point[0]),
                   default=None)

    def _resolve_agent_emergency(self, agent: Any, target: Any) -> None:
        for emergency in tuple(self.emergency_manager.active_emergencies):
            if emergency.assigned_agent is agent and emergency.target is target:
                self.emergency_manager.resolve_emergency(emergency)
        for event in tuple(self.event_manager.active_events):
            if isinstance(event, Accident) and event.victim is target:
                event.resolve(self.scheduler.tick)
            elif isinstance(event, Failure) and event.building is target:
                event.resolve(self.scheduler.tick)

    def _construction_entry(self, project: ConstructionProject, agent: Any) -> tuple[int, int] | None:
        x, y = project.position
        width, height = project.footprint
        candidates = set()
        for dy in range(height):
            for dx in range(width):
                for tile in self.mars_map.walkable_neighbors(x + dx, y + dy):
                    if not tile.occupied:
                        candidates.add((tile.x, tile.y))
        return min(candidates, key=lambda point: abs(point[0] - agent.position[0])
                   + abs(point[1] - agent.position[1]), default=None)

    def _complete_construction(self, project: ConstructionProject, agent: Any) -> bool:
        module_name = re.sub(r"(?<!^)(?=[A-Z])", "_", project.building_name).lower()
        building_class = getattr(importlib.import_module(f"colony.buildings.{module_name}"), project.building_name)
        building_id = max((int(key) for key in self.buildings_by_id if isinstance(key, int)), default=0) + 1
        building = building_class(building_id=building_id, position=project.position)
        if not self.place_building(building, *project.footprint):
            return False
        project.progress = 100.0
        self.construction_manager.complete_project(project)
        if hasattr(agent, "structures_built"):
            agent.structures_built += 1
        return True

    def _apply_autonomous_activity(self, agent: Any, action: str) -> None:
        target_kind = {"sleep": "habitat", "recreation": "habitat",
                       "recharge": "battery", "maintenance": "workshop"}.get(action)
        if target_kind:
            target = self._nearest_habitat_entry(agent) if target_kind == "habitat" else self._nearest_facility_entry(agent, target_kind)
            if target is not None and tuple(agent.position) != target:
                if not agent.moving:
                    if not self.move_agent_to(agent, target):
                        agent.decision_reason = f"The {target_kind} is unreachable; waiting for a safe route."
                        agent.current_activity = "Waiting"
                        return
                agent.current_activity = "Walking"
                agent.state = type(agent.state).WALKING
                return
        if action == "sleep":
            agent.current_activity = "Sleeping"
            agent.state = type(agent.state).SLEEPING
        elif action == "eat":
            agent.current_activity = "Eating"
            agent.state = type(agent.state).EATING
        elif action == "drink":
            agent.current_activity = "Drinking"
            agent.state = type(agent.state).DRINKING
        elif action == "socialize":
            agent.current_activity = "Seeking colleague"
            agent.state = type(agent.state).IDLE
        elif action == "recreation":
            agent.current_activity = "Recreation"
            agent.state = type(agent.state).IDLE
        elif action == "recharge":
            agent.current_activity = "Charging"
            if hasattr(agent, "robot_status"):
                agent.robot_status = type(agent.robot_status).CHARGING
            agent.state = type(agent.state).IDLE
        elif action == "maintenance":
            agent.current_activity = "Maintenance"
            agent.state = type(agent.state).IDLE
        elif action == "emergency":
            agent.current_activity = "Emergency Response"
            agent.state = type(agent.state).EMERGENCY
        else:
            agent.current_activity = "Available"
            agent.state = type(agent.state).IDLE

    def _nearest_habitat_entry(self, agent: Any) -> tuple[int, int] | None:
        if self._habitat_entries_cache is None:
            entries = set()
            for building in self.buildings_by_id.values():
                if "habitat" not in type(building).__name__.lower():
                    continue
                for tile in self.mars_map.tiles.values():
                    if tile.building is building:
                        entries.update((neighbor.x, neighbor.y)
                                       for neighbor in self.mars_map.walkable_neighbors(tile.x, tile.y))
            self._habitat_entries_cache = tuple(sorted(entries))
        return min(self._habitat_entries_cache,
                   key=lambda pos: abs(agent.position[0] - pos[0]) + abs(agent.position[1] - pos[1]),
                   default=None)

    def _nearest_facility_entry(self, agent: Any, name: str) -> tuple[int, int] | None:
        if name not in self._facility_entries_cache:
            entries = set()
            for building in self.buildings_by_id.values():
                if name.lower() not in type(building).__name__.lower():
                    continue
                for tile in self.mars_map.tiles.values():
                    if tile.building is building:
                        entries.update((neighbor.x, neighbor.y)
                                       for neighbor in self.mars_map.walkable_neighbors(tile.x, tile.y))
            self._facility_entries_cache[name] = tuple(sorted(entries))
        return min(self._facility_entries_cache[name],
                   key=lambda pos: abs(agent.position[0] - pos[0]) + abs(agent.position[1] - pos[1]),
                   default=None)

    def _advance_agent_movement(self, agent: Any) -> None:
        if agent.moving and agent.path:
            source, destination = tuple(agent.position), tuple(agent.path[0])
            if hasattr(agent, "battery_level"):
                tile = self.mars_map.get_tile(*destination)
                cargo_penalty = min(.5, getattr(agent, "carrying_weight", 0.0) * .005)
                energy = .12 * max(.5, float(tile.terrain.movement_cost if tile is not None else 1.0)) + cargo_penalty
                if agent.battery_level < energy:
                    agent.consume_battery(agent.battery_level)
                    agent.moving = False
                    agent.path.clear()
                    return
            if self.mars_map.move_agent(agent, source, destination):
                agent.position = destination
                agent.path.pop(0)
                agent.distance_travelled += dist(source, destination)
                if hasattr(agent, "consume_battery"):
                    agent.consume_battery(energy)
                task = getattr(agent, "current_task", None)
                request_id = task.metadata.get("logistics_request_id") if task is not None else None
                if request_id:
                    request = next((item for item in self.logistics_manager.delivery_queue
                                    if item.request_id == request_id), None)
                    if request is not None and task.metadata.get("phase") == "deliver":
                        route_length = max(1, int(task.metadata.get("delivery_route_length", 0)))
                        request.travel_progress = min(100.0,
                                                      100.0 * (route_length - len(agent.path)) / route_length)
                if not agent.path:
                    agent.stop()

    @staticmethod
    def _award_task_experience(agent: Any, task: Any) -> None:
        if hasattr(agent, "gain_experience"):
            agent.gain_experience(10)
            skill = next(iter(task.required_skills), None)
            if skill is None:
                skill = task.metadata.get("skill")
            if skill:
                progress = agent.metadata.setdefault("skill_progress", {})
                progress[skill] = progress.get(skill, 0) + 1
                if progress[skill] >= 3:
                    agent.improve_skill(skill, 1)
                    progress[skill] = 0

    @staticmethod
    def _agent_can_take(agent: Any, task: Any) -> bool:
        skills = getattr(agent, "skill_levels", {})
        return all(skills.get(name, 0) >= level for name, level in task.required_skills.items())

    def step_core(
        self,
    ) -> None:

        self.power_grid.step()

        self.resource_manager.step()

    def step_resources(
        self,
    ) -> None:

        self.construction_manager.step()

        self.logistics_manager.step()

        self.maintenance_manager.step()

    def step_population(
        self,
    ) -> None:

        self.population_manager.step()

        self.ai_manager.step()

        self.task_manager.step()

    def step_colony(
        self,
    ) -> None:

        self.research_manager.step()

        self.economy_manager.step()

        self.emergency_manager.step()

    def step_events(
        self,
    ) -> None:

        self.event_manager.step()

        self.accident_manager.step()

        self.failure_manager.step()

        self.random_event_manager.step()

    # ========================================================
    # Scheduler Events
    # ========================================================

    def process_scheduler_events(
        self,
    ) -> None:

        scheduler = self.scheduler

        if scheduler.new_hour:

            self.hourly_update()

        if scheduler.new_day:

            self.daily_update()

    def hourly_update(
        self,
    ) -> None:

        self.day_night.step(self.day_night.sol_length / self.scheduler.hours_per_day)
        resources = self.resource_manager.resources
        before = {name: (resource.total_produced, resource.total_consumed)
                  for name, resource in resources.items()}
        history_before = dict(self.resource_manager.consumption_history)
        producers = [b for b in self.buildings_by_id.values()
                     if type(b).__name__ in {"SolarArray", "Reactor"}]
        others = [b for b in self.buildings_by_id.values() if b not in producers]
        for building in producers:
            if type(building).__name__ == "SolarArray":
                weather_modifier = {"Clear": 1.0, "Cloudy": .82, "Windy": .92, "Dusty": .65,
                                    "Dust Storm": .3, "Cold Front": .8}.get(self.weather.weather.value, 1.0)
                building.sunlight_efficiency = self.day_night.solar_efficiency * weather_modifier
                if self.weather.is_storm:
                    building.apply_dust(.02)
                else:
                    building.clean_panels(.005)
            if type(building).__name__ == "Reactor":
                fuel_before = building.fuel.current_amount
                generated = building.generate_power()
                if building.fuel.current_amount < fuel_before:
                    building.generate_heat()
            else:
                previous = getattr(building, "total_power_generated", 0.0)
                building.hourly_update()
                generated = getattr(building, "total_power_generated", 0.0) - previous
                building.metadata["last_power_generation"] = max(0.0, generated)
                continue
            building.hourly_update()
            building.metadata["last_power_generation"] = max(0.0, generated)
        self.power_grid.hourly_update()
        for building in others:
            building.hourly_update()
            if type(building).__name__ == "Mine":
                self._operate_mine(building)
            elif type(building).__name__ == "WaterPlant":
                self._operate_water_plant(building)
        for agent in self.agents_by_id.values():
            if not getattr(agent, "alive", True):
                continue
            if hasattr(agent, "suit_oxygen"):
                oxygen_demand = 0.5 * self.needs_intensity
                oxygen_ok = oxygen_demand <= 0 or self.resource_manager.consume("Oxygen", oxygen_demand)
                agent.hourly_update(self.needs_intensity)
                if agent.outside:
                    tile = self.mars_map.get_tile(*agent.position)
                    exposure = (tile.radiation if tile is not None else .05) * self.weather.radiation_modifier
                    agent.radiation += exposure * self.radiation_severity
                    if self.weather.temperature < -100:
                        agent.change_stress(.5 * self.radiation_severity)
                if oxygen_ok:
                    agent.refill_oxygen(oxygen_demand)
                else:
                    agent.consume_oxygen(10.0)
                if not agent.alive and not agent.metadata.get("population_removed", False):
                    population = resources.get("Population")
                    if population is not None:
                        population.consume(1.0)
                        self.population_manager.update_population()
                    agent.metadata["population_removed"] = True
                if self.needs_intensity > 0 and not agent.busy and agent.thirst >= 55:
                    if self.resource_manager.consume("Water", self.needs_intensity):
                        agent.drink(25.0 * self.needs_intensity)
                        agent.activity_until_tick = self.scheduler.tick + max(1, self.scheduler.ticks_per_hour // 10)
                    elif agent.thirst >= 90:
                        agent.take_damage(.5)
                if self.needs_intensity > 0 and not agent.busy and agent.hunger >= 55:
                    if self.resource_manager.consume("Food", self.needs_intensity):
                        agent.eat(25.0 * self.needs_intensity)
                        agent.activity_until_tick = self.scheduler.tick + max(1, self.scheduler.ticks_per_hour // 10)
                    elif agent.hunger >= 90:
                        agent.take_damage(.25)
                if not agent.busy:
                    decision = self.autonomy_manager.decide(agent, self.scheduler.hour,
                                                            bool(self.emergency_manager.active_emergencies))
                    if decision.action == "sleep":
                        shelter = self._nearest_habitat_entry(agent)
                        if shelter is None or tuple(agent.position) == shelter:
                            agent.sleep(20.0)
                            agent.current_activity = "Sleeping"
                    elif decision.action == "recreation":
                        agent.recreation_need = max(0.0, agent.recreation_need - 12.0)
                        agent.change_stress(-1.0)
                        agent.current_activity = "Recreation"
                        agent.activity_until_tick = self.scheduler.tick + self.scheduler.ticks_per_hour
            else:
                agent.hourly_update()
                if getattr(agent, "current_activity", "") == "Charging":
                    charging_entry = self._nearest_facility_entry(agent, "battery")
                    if charging_entry is not None and tuple(agent.position) == charging_entry:
                        banks = [b for b in self.buildings_by_id.values()
                                 if type(b).__name__ == "Battery" and getattr(b, "stored_energy", 0) > 0]
                        if banks:
                            delivered = banks[0].discharge(min(20.0, agent.battery_capacity - agent.battery_level))
                            agent.recharge(delivered)
                            if delivered <= 0:
                                agent.decision_reason = "The nearby battery bank has no discharge reserve."
                elif getattr(agent, "current_activity", "") == "Maintenance":
                    workshop = self._nearest_facility_entry(agent, "workshop")
                    if workshop is not None and tuple(agent.position) == workshop:
                        agent.maintenance(10.0)
        self._service_research()
        event_titles = [getattr(event, "name", "Colony event")
                        for event in self.event_manager.active_events]
        self.social_manager.update_hour(
            list(self.agents_by_id.values()), self.scheduler.tick, self.scheduler.ticks_per_hour,
            {"warnings": sorted(self.resource_manager.shortages), "events": event_titles,
             "hour": self.scheduler.hour, "sol": self.scheduler.sol},
        )
        for name, resource in resources.items():
            resource.hourly_update()
            produced_before, consumed_before = before[name]
            produced = resource.total_produced - produced_before
            consumed = resource.total_consumed - consumed_before
            already_ledgered = (self.resource_manager.consumption_history.get(name, 0.0)
                                - history_before.get(name, 0.0))
            consumed = max(0.0, consumed - already_ledgered)
            if produced > 0:
                self.resource_manager.production_history[name] = (
                    self.resource_manager.production_history.get(name, 0.0) + produced)
            if consumed > 0:
                self.resource_manager.consumption_history[name] = (
                    self.resource_manager.consumption_history.get(name, 0.0) + consumed)

        for manager in self.managers:

            manager.hourly_update()

        if self.autonomy_manager.enabled:
            self.ai_manager.assess_and_plan(self)

    def _operate_mine(self, mine: Any) -> float:
        """Extract only finite ore currently present in MarsMap deposits."""
        return self._operate_deposit_processor(mine, "Minerals", "extract_minerals")

    def _operate_water_plant(self, plant: Any) -> float:
        """Produce water only by processing finite mapped water deposits."""
        return self._operate_deposit_processor(plant, "Water", "generate_water")

    def _operate_deposit_processor(self, building: Any, resource_name: str, operation: str) -> float:
        position = building.metadata.get(f"{resource_name.lower()}_deposit_position")
        if position is not None:
            position = tuple(position)
        tile = self.mars_map.get_tile(*position) if position is not None else None
        if tile is None or tile.resource_deposit.get(resource_name, 0.0) <= 0.0:
            candidates = [(abs(x - building.position[0]) + abs(y - building.position[1]), y, x, candidate)
                         for (x, y), candidate in self.mars_map.tiles.items()
                         if candidate.resource_deposit.get(resource_name, 0.0) > 0.0]
            if not candidates:
                building.metadata.pop(f"{resource_name.lower()}_deposit_position", None)
                return 0.0
            _distance, y, x, tile = min(candidates, key=lambda item: (item[0], item[1], item[2]))
            position = (x, y)
            building.metadata[f"{resource_name.lower()}_deposit_position"] = list(position)
        available = tile.resource_deposit.get(resource_name, 0.0)
        produced = getattr(building, operation)(available)
        if produced > 0.0:
            depleted = self.mars_map.remove_resource(*position, resource_name, produced)
            if depleted < produced:
                raise RuntimeError(f"{type(building).__name__} produced more {resource_name} than its deposit contained")
        return produced

    def _service_research(self) -> None:
        """Assign queued research to real scientists and advance only at a lab."""
        labs = [building for building in self.buildings_by_id.values()
                if type(building).__name__ == "Laboratory" and building.operational]
        if not labs:
            return
        scientists = [agent for agent in self.agents_by_id.values()
                      if type(agent).__name__ == "Scientist" and getattr(agent, "alive", True)]
        assigned = {project.assigned_scientist.unique_id for project in self.research_manager.active_projects
                    if project.assigned_scientist is not None and not project.completed}
        for project in sorted(self.research_manager.research_queue, key=lambda item: -item.priority):
            scientist = next((agent for agent in scientists if agent.unique_id not in assigned
                              and agent.current_task is None), None)
            if scientist is None:
                break
            lab = min(labs, key=lambda item: abs(scientist.position[0] - item.position[0])
                      + abs(scientist.position[1] - item.position[1]))
            scientist.assign_laboratory(lab)
            if self.research_manager.assign_project(scientist, project):
                assigned.add(scientist.unique_id)
        science = self.resource_manager.resource("Science Points")
        if science is None:
            return
        for project in tuple(self.research_manager.active_projects):
            scientist = project.assigned_scientist
            lab = getattr(scientist, "assigned_laboratory", None)
            if scientist is None or lab not in labs:
                continue
            entry = self._nearest_facility_entry(scientist, "laboratory")
            if entry is None or tuple(scientist.position) != entry or scientist.moving:
                continue
            if not scientist.research():
                continue
            work_points = min(science.current_amount, max(1.0, float(scientist.skill_level("science"))))
            if work_points > 0 and self.resource_manager.consume("Science Points", work_points):
                self.research_manager.research_points += work_points
                self.research_manager.advance_project(project, work_points)
                scientist.current_activity = "Operating Equipment"
                if project.completed:
                    self._apply_research_unlock(project.name)

    def _apply_research_unlock(self, name: str) -> None:
        """Apply completed technology to existing, authoritative colony entities."""
        if name == "Solar Efficiency":
            for building in self.buildings_by_id.values():
                if type(building).__name__ == "SolarArray":
                    building.power_output *= 1.15
        elif name == "Crop Yield":
            for building in self.buildings_by_id.values():
                if type(building).__name__ == "Greenhouse":
                    building.growth_bonus = min(2.0, building.growth_bonus + .2)
        elif name == "Oxygen Recovery":
            for building in self.buildings_by_id.values():
                if type(building).__name__ == "OxygenGenerator":
                    building.oxygen_output *= 1.15
        elif name == "Water Recovery":
            for building in self.buildings_by_id.values():
                if type(building).__name__ == "WaterPlant":
                    building.water_output *= 1.15
        elif name == "Robotics":
            for agent in self.agents_by_id.values():
                if "robot" in type(agent).__name__.lower():
                    agent.efficiency = min(2.0, agent.efficiency * 1.1)
        elif name == "Medical Care":
            for building in self.buildings_by_id.values():
                if type(building).__name__ == "MedicalBay":
                    building.medicine_efficiency = min(2.0, building.medicine_efficiency + .1)

    def daily_update(
        self,
    ) -> None:

        self.weather.randomize()
        for agent in self.agents_by_id.values():
            agent.daily_update()
        for manager in self.managers:

            manager.daily_update()
        self._process_arrivals()

    def _process_arrivals(self) -> None:
        """Admit only configured arrivals for whom housing and life support exist."""
        for index, (sol, human_count, robot_count) in enumerate(self.arrival_schedule):
            if index in self.processed_arrivals or self.scheduler.sol < sol:
                continue
            humans = sum(hasattr(agent, "suit_oxygen") for agent in self.agents_by_id.values())
            life_support = all(self.resource_manager.amount(name) >= human_count * per_person
                               for name, per_person in (("Oxygen", 5.0), ("Water", 3.0), ("Food", 2.0)))
            if self.population_manager.housing_available < human_count or not life_support:
                continue
            open_tiles = [(x, y) for y in range(self.mars_map.height) for x in range(self.mars_map.width)
                          if (tile := self.mars_map.get_tile(x, y)) is not None and tile.walkable
                          and not tile.occupied and tile.building is None and not tile.agents]
            if len(open_tiles) < human_count + robot_count:
                continue
            from colony.agents.astronaut import Astronaut
            from colony.agents.robot import Robot
            from colony.agents.engineer import Engineer
            from colony.agents.scientist import Scientist
            from colony.agents.farmer import Farmer
            from colony.agents.medic import Medic
            crew_classes = (Engineer, Scientist, Farmer, Medic, Astronaut)
            human_ids = [agent.unique_id for agent in self.agents_by_id.values()
                         if hasattr(agent, "suit_oxygen")]
            next_human_id = max(human_ids, default=0) + 1
            next_robot_id = max((agent.unique_id for agent in self.agents_by_id.values()
                                 if "robot" in type(agent).__name__.lower()), default=1000) + 1
            for offset in range(human_count):
                cls = crew_classes[(humans + offset) % len(crew_classes)]
                self.register_agent(cls(unique_id=next_human_id + offset,
                    name=f"{cls.__name__} {next_human_id + offset}", profession=cls.__name__,
                    position=open_tiles.pop(0)))
            for offset in range(robot_count):
                self.register_agent(Robot(unique_id=next_robot_id + offset,
                    name=f"Arrival Rover {next_robot_id + offset}", profession="Colony Robot",
                    serial_number=f"HAB-R{next_robot_id + offset:03}", position=open_tiles.pop(0)))
            self.processed_arrivals.add(index)
            self.event_manager.publish(BaseEvent(name="Crew arrival",
                description=f"A scheduled transport delivered {human_count} crew and {robot_count} robots.",
                severity=EventSeverity.INFO, created_tick=self.scheduler.tick,
                event_id=f"crew-arrival-{index + 1:04d}",
                metadata={"humans": human_count, "robots": robot_count, "sol": self.scheduler.sol}))
            self.population_manager.update_population()
            self.population_manager.update_housing()

    # ========================================================
    # Colony Status
    # ========================================================

    @property
    def initialized(
        self,
    ) -> bool:

        return all(manager.initialized for manager in self.managers)

    @property
    def running(
        self,
    ) -> bool:

        return self.initialized

    @property
    def current_tick(
        self,
    ) -> int:

        return self.scheduler.tick

    @property
    def current_hour(
        self,
    ) -> int:

        return self.scheduler.hour

    @property
    def current_day(
        self,
    ) -> int:

        return self.scheduler.day

    @property
    def current_month(
        self,
    ) -> int:

        return self.scheduler.month

    @property
    def current_year(
        self,
    ) -> int:

        return self.scheduler.year

    @property
    def manager_count(
        self,
    ) -> int:

        return len(
            self.managers,
        )

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        return {
            "scheduler": self.scheduler.statistics(),
            "events": self.event_manager.statistics(),
            "accidents": self.accident_manager.statistics(),
            "failures": self.failure_manager.statistics(),
            "random_events": self.random_event_manager.statistics(),
            "manager_count": self.manager_count,
            "map": self.mars_map.statistics(),
            "agents": len(self.agents_by_id),
            "buildings": len(self.buildings_by_id),
            "initialized": self.initialized,
            "power_grid": self.power_grid.statistics(),
            "resources": self.resource_manager.statistics(),
            "population": self.population_manager.statistics(),
            "construction": self.construction_manager.statistics(),
            "logistics": self.logistics_manager.statistics(),
            "research": self.research_manager.statistics(),
            "economy": self.economy_manager.statistics(),
            "emergency": self.emergency_manager.statistics(),
            "maintenance": self.maintenance_manager.statistics(),
            "ai": self.ai_manager.statistics(),
            "tasks": self.task_manager.statistics(),
            "autonomy": self.autonomy_manager.statistics(),
            "social": self.social_manager.statistics(),
        }

    # ========================================================
    # Debug Statistics
    # ========================================================

    def debug_statistics(
        self,
    ) -> dict:

        return {

            "scheduler":
                self.scheduler.statistics(),

            "events":
                self.event_manager.debug_statistics(),

            "accidents":
                self.accident_manager.debug_statistics(),

            "failures":
                self.failure_manager.debug_statistics(),

            "random_events":
                self.random_event_manager.debug_statistics(),

            "manager_count":
                self.manager_count,

            "initialized":
                self.initialized,

            "power_grid":
                self.power_grid.debug_statistics(),

            "resources":
                self.resource_manager.debug_statistics(),

            "population":
                self.population_manager.debug_statistics(),

            "construction":
                self.construction_manager.debug_statistics(),

            "logistics":
                self.logistics_manager.debug_statistics(),

            "research":
                self.research_manager.debug_statistics(),

            "economy":
                self.economy_manager.debug_statistics(),

            "emergency":
                self.emergency_manager.debug_statistics(),

            "maintenance":
                self.maintenance_manager.debug_statistics(),

            "ai":
                self.ai_manager.debug_statistics(),

            "tasks":
                self.task_manager.debug_statistics(),

        }

    # ========================================================
    # Utility
    # ========================================================

    def reset(
        self,
    ) -> None:

        for manager in self.managers:

            manager.reset()

        self.agents_by_id.clear()
        self.buildings_by_id.clear()
        self.mars_map = MarsMap(self.mars_map.width, self.mars_map.height)

    def serialize(
        self,
    ) -> dict:

        return {
            "mars_map": self.mars_map.serialize(),
            "weather": self.weather.serialize(),
            "day_night": self.day_night.serialize(),
            "world_seed": self.world_seed,
            "needs_intensity": self.needs_intensity,
            "radiation_severity": self.radiation_severity,
            "colony_name": self.colony_name,
            "colony_id": self.colony_id,
            "arrival_schedule": self.arrival_schedule,
            "processed_arrivals": sorted(self.processed_arrivals),
            "discovered_deposits": [dict(item) for item in self.discovered_deposits],
            "exploration_reports": [dict(item) for item in self.exploration_reports],
            "agents": [self._serialize_agent(a) for a in self.agents_by_id.values()],
            "buildings": [{"class": type(b).__module__ + "." + type(b).__name__, "data": self._serialize_building(b),
                           "footprint": (max((t.local_x for t in self.mars_map.tiles.values() if t.building is b), default=0) + 1,
                                         max((t.local_y for t in self.mars_map.tiles.values() if t.building is b), default=0) + 1)}
                          for b in self.buildings_by_id.values()],
            "scheduler": self.scheduler.serialize(),
            "managers": self._serialize_managers(),
        }

    def _serialize_managers(self) -> dict:
        result = {}
        for name, manager in zip(self._manager_names(), self.managers):
            values = {"enabled": manager.enabled, "initialized": manager.initialized,
                      "state": manager.state.value, "tick_count": manager.tick_count,
                      "hour_count": manager.hour_count, "day_count": manager.day_count,
                      "update_count": manager.update_count, "error_count": manager.error_count}
            for attr, value in vars(manager).items():
                if isinstance(value, Enum):
                    values[attr] = value.value
                elif isinstance(value, (str, int, float, bool, type(None))):
                    values[attr] = value
                elif isinstance(value, dict) and all(isinstance(k, (str, int)) and
                     isinstance(v, (str, int, float, bool, type(None))) for k, v in value.items()):
                    values[attr] = dict(value)
                elif isinstance(value, (list, tuple, set)) and all(
                    isinstance(item, (str, int, float, bool, type(None))) for item in value
                ):
                    values[attr] = sorted(value, key=str) if isinstance(value, set) else list(value)
            result[name] = values
        result["resource_manager"] = self.resource_manager.serialize()
        result["event_manager"] = self.event_manager.serialize()
        result["social_manager"] = self.social_manager.serialize()
        result["power_grid"].update({
            "producers": [getattr(obj, "building_id", None) for obj in self.power_grid.producers],
            "consumers": [getattr(obj, "building_id", None) for obj in self.power_grid.consumers],
            "batteries": [getattr(obj, "building_id", None) for obj in self.power_grid.batteries],
            "power_resource": "Power",
        })
        result["task_manager"].update({
            key: [self._serialize_task(task) for task in getattr(self.task_manager, key)]
            for key in ("tasks", "completed_tasks", "failed_tasks", "cancelled_tasks")
        })
        result["ai_manager"].update({"alert_level": self.ai_manager.alert_level.value,
            "colony_score": self.ai_manager.colony_score,
            "recommendations": list(self.ai_manager.recommendations),
            "last_resource_amounts": dict(self.ai_manager.last_resource_amounts),
            "resource_forecasts": deepcopy(self.ai_manager.resource_forecasts),
            "goals": deepcopy(self.ai_manager.goals),
            "decisions": deepcopy(self.ai_manager.decisions),
            "planning_interval_hours": self.ai_manager.planning_interval_hours,
            "last_planning_tick": self.ai_manager.last_planning_tick})
        result["population_manager"].pop("population", None)
        result["construction_manager"].update({
            "construction_queue": [self._serialize_construction(p) for p in self.construction_manager.construction_queue],
            "active_projects": [self._serialize_construction(p) for p in self.construction_manager.active_projects]})
        result["research_manager"].update({
            key: [self._serialize_research(p) for p in getattr(self.research_manager, key)]
            for key in ("research_queue", "active_projects", "completed_projects")})
        result["maintenance_manager"]["maintenance_queue"] = [
            {"building_id": req.building.building_id, "priority": req.priority,
             "repair_amount": req.repair_amount, "completed": req.completed,
             "assigned_agent": getattr(req.assigned_agent, "unique_id", None)}
            for req in self.maintenance_manager.maintenance_queue]
        result["logistics_manager"]["delivery_queue"] = [
            {"resource": req.resource, "amount": req.amount, "priority": req.priority,
             "completed": req.completed, "source": self._entity_reference(req.source),
             "destination": self._entity_reference(req.destination),
             "assigned_robot": getattr(req.assigned_robot, "unique_id", None),
             "request_id": req.request_id, "loading_progress": req.loading_progress,
             "travel_progress": req.travel_progress, "unloading_progress": req.unloading_progress,
             "failed": req.failed}
            for req in self.logistics_manager.delivery_queue]
        result["emergency_manager"].update({
            "emergency_queue": [self._serialize_emergency(e) for e in self.emergency_manager.emergency_queue],
            "active_emergencies": [self._serialize_emergency(e) for e in self.emergency_manager.active_emergencies]})
        return result

    @staticmethod
    def _entity_reference(value):
        if hasattr(value, "unique_id"):
            return {"agent": value.unique_id}
        if hasattr(value, "building_id"):
            return {"building": value.building_id}
        return value if isinstance(value, (str, int, float, bool, type(None))) else None

    def _serialize_task(self, task):
        return {**task.serialize(), "target": self._entity_reference(task.target),
                "assigned_agent": getattr(task.assigned_agent, "unique_id", None)}

    @staticmethod
    def _serialize_construction(project):
        return {"building_name": project.building_name, "position": project.position,
                "required_resources": dict(project.required_resources), "progress": project.progress,
                "priority": project.priority, "completed": project.completed,
                "assigned_agent": getattr(project.assigned_agent, "unique_id", None),
                "task_id": project.task_id, "footprint": project.footprint}

    @staticmethod
    def _serialize_research(project):
        return {"name": project.name, "description": project.description,
                "required_points": project.required_points, "progress": project.progress,
                "priority": project.priority, "completed": project.completed,
                "unlocked": project.unlocked,
                "category": project.category, "prerequisites": project.prerequisites,
                "assigned_scientist": getattr(project.assigned_scientist, "unique_id", None)}

    def _serialize_emergency(self, emergency):
        return {"title": emergency.title, "description": emergency.description,
                "severity": emergency.severity.value, "location": emergency.location,
                "source": self._entity_reference(emergency.source),
                "target": self._entity_reference(emergency.target),
                "assigned_agent": getattr(emergency.assigned_agent, "unique_id", None),
                "resolved": emergency.resolved}

    def restore_serialized(self, data: dict) -> None:
        """Restore map and reconnect manager scheduler references."""
        saved_managers = data.get("managers", data)
        self.world_seed = int(data.get("world_seed", self.world_seed))
        self.needs_intensity = float(data.get("needs_intensity", self.needs_intensity))
        self.radiation_severity = float(data.get("radiation_severity", self.radiation_severity))
        self.colony_name = data.get("colony_name", self.colony_name)
        self.colony_id = data.get("colony_id", self.colony_id)
        self.arrival_schedule = tuple(tuple(item) for item in data.get("arrival_schedule", ()))
        self.processed_arrivals = set(data.get("processed_arrivals", ()))
        self.discovered_deposits = [dict(item) for item in data.get("discovered_deposits", ())]
        self.exploration_reports = [dict(item) for item in data.get("exploration_reports", ())]
        if data.get("weather"):
            self.weather = WeatherSystem.deserialize(data["weather"])
        if data.get("day_night"):
            self.day_night = DayNightCycle.deserialize(data["day_night"])
        if saved_managers.get("resource_manager"):
            scheduler = self.scheduler
            self.resource_manager = ResourceManager.deserialize(saved_managers["resource_manager"])
            self.resource_manager.scheduler = scheduler
        self.power_grid.producers.clear()
        self.power_grid.consumers.clear()
        self.power_grid.batteries.clear()
        self.population_manager.housing_capacity = 0
        self.ai_manager.clear()
        self.maintenance_manager.clear()
        self.logistics_manager.clear()
        if data.get("mars_map"):
            self.mars_map = MarsMap.deserialize(data["mars_map"])
            # Entity occupancy is rebuilt from its authoritative registry below.
            for tile in self.mars_map.tiles.values():
                tile.occupied = False
                tile.walkable = tile.terrain.walkable
        self.agents_by_id.clear()
        self.buildings_by_id.clear()
        self._restoring_entities = True
        pending_tasks: dict[int, tuple[Any, Any]] = {}
        pending_agent_links: dict[int, dict[str, Any]] = {}
        for item in data.get("agents", ()):
            cls = self._saved_class(item["class"])
            agent_data = deepcopy(item["data"])
            current_task_id = agent_data.pop("$current_task", None)
            queued_task_ids = agent_data.pop("$task_queue", ())
            entity_links = agent_data.pop("$entity_links", {})
            agent_data["current_task"] = None
            agent_data["task_queue"] = []
            for attr in entity_links:
                agent_data[attr] = None
            agent = cls.deserialize(agent_data)
            self.register_agent(agent)
            pending_tasks[agent.unique_id] = (current_task_id, queued_task_ids)
            pending_agent_links[agent.unique_id] = entity_links
        for item in data.get("buildings", ()):
            cls = self._saved_class(item["class"])
            building_data = deepcopy(item["data"])
            for attr, value in list(building_data.items()):
                if isinstance(value, dict) and "$resource_ref" in value:
                    resource = self.resource_manager.resource(value["$resource_ref"])
                    if resource is None:
                        raise ValueError(f"Missing saved resource {value['$resource_ref']!r}")
                    building_data[attr] = resource
                elif isinstance(value, dict) and "$resource" in value:
                    resource_class = self._saved_class(value["$resource"])
                    building_data[attr] = resource_class.deserialize(value["data"])
            building = cls.deserialize(building_data)
            if not self.place_building(building, *item.get("footprint", cls.default_footprint)):
                raise ValueError(f"Saved building {building!r} cannot be restored")
        self._restoring_entities = False
        saved_managers = data.get("managers", data)
        self._restore_manager_state(saved_managers)
        for agent_id, links in pending_agent_links.items():
            agent = self.agents_by_id[agent_id]
            for attr, reference in links.items():
                setattr(agent, attr, self._resolve_entity(reference))
        task_by_id = {task.task_id: task for task in self.task_manager.tasks
                      + self.task_manager.completed_tasks + self.task_manager.failed_tasks
                      + self.task_manager.cancelled_tasks}
        for task_data in saved_managers.get("task_manager", {}).get("tasks", []):
            task = task_by_id.get(task_data.get("task_id"))
            if task is not None:
                task.location = tuple(task.location) if task.location is not None else None
                task.target = self._resolve_entity(task_data.get("target"))
                task.assigned_agent = self.agents_by_id.get(task_data.get("assigned_agent"))
        for agent_id, (current_id, queued_ids) in pending_tasks.items():
            agent = self.agents_by_id[agent_id]
            agent.current_task = task_by_id.get(current_id)
            agent.task_queue = [task_by_id[task_id] for task_id in queued_ids if task_id in task_by_id]
            if agent.current_task is not None:
                agent.current_task.assigned_agent = agent
                self.task_manager.assignments[agent_id] = agent.current_task
        for event in self.event_manager.active_events + self.event_manager.archived_events:
            for field_name, value in vars(event).items():
                if isinstance(value, dict) and ("$agent" in value or "$building" in value):
                    setattr(event, field_name, self._resolve_entity(value))
        self.accident_manager.astronauts = [agent for agent in self.agents_by_id.values()
                                            if hasattr(agent, "suit_oxygen")]
        self.accident_manager.robots = [agent for agent in self.agents_by_id.values()
                                        if "robot" in type(agent).__name__.lower()]
        self.failure_manager.buildings = list(self.buildings_by_id.values())
        restored_events = self.event_manager.active_events + self.event_manager.archived_events
        self.accident_manager.accidents = [event for event in restored_events if isinstance(event, Accident)]
        self.failure_manager.failures = [event for event in restored_events if isinstance(event, Failure)]
        self.random_event_manager.events = [event for event in restored_events if isinstance(event, RandomEvent)]
        for manager in self.managers:
            manager.scheduler = self.scheduler
        for name, manager in zip(self._manager_names(), self.managers):
            if name in saved_managers:
                self._restore_manager_scalars(manager, saved_managers[name])
        self.connect_managers()
        self.register_visible_deposits()

    def _serialize_agent(self, agent: Any) -> dict:
        data = {}
        for attribute in fields(agent):
            name = attribute.name
            value = getattr(agent, name)
            if name == "state" or isinstance(value, Enum):
                data[name] = value.value
            elif name == "inventory":
                data[name] = {item_name: {"quantity": item.quantity, "weight": item.weight}
                              for item_name, item in value.items()}
            elif name in {"current_task", "task_queue"}:
                data[name] = None if name == "current_task" else []
            elif isinstance(value, dict):
                data[name] = {key: self._serialize_plain(item) for key, item in value.items()}
            elif isinstance(value, list):
                data[name] = [self._serialize_plain(item) for item in value]
            else:
                data[name] = self._serialize_plain(value)
        links = {}
        for attr, value in vars(agent).items():
            if attr in {"current_task", "task_queue"}:
                continue
            reference = self._entity_reference(value)
            if isinstance(reference, dict):
                links[attr] = reference
                data[attr] = None
        data["$entity_links"] = links
        data["$current_task"] = getattr(agent.current_task, "task_id", None)
        data["$task_queue"] = [task.task_id for task in agent.task_queue if hasattr(task, "task_id")]
        return {"class": f"{type(agent).__module__}.{type(agent).__name__}", "data": data}

    def _serialize_plain(self, value):
        reference = self._entity_reference(value)
        if isinstance(reference, dict):
            return {"$entity": reference}
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        return None

    def _serialize_building(self, building: Any) -> dict:
        data = building.serialize()
        for attr, value in vars(building).items():
            if isinstance(value, BaseResource):
                if self.resource_manager.resource(value.name) is value:
                    data[attr] = {"$resource_ref": value.name}
                else:
                    data[attr] = {"$resource": f"{type(value).__module__}.{type(value).__name__}",
                                  "data": value.serialize()}
        return data

    def _restore_manager_state(self, data: dict) -> None:
        for key in self._manager_names():
            if key not in data:
                continue
            manager_data = data[key]
            if key == "task_manager":
                self.task_manager = TaskManager.deserialize(deepcopy(manager_data))
            elif key == "event_manager":
                self.event_manager = EventManager.deserialize(deepcopy(manager_data))
            elif key == "ai_manager":
                self.ai_manager = AIManager.deserialize(deepcopy(manager_data))
                for agent in self.agents_by_id.values():
                    self.ai_manager.register_agent(agent)
                for building in self.buildings_by_id.values():
                    self.ai_manager.register_building(building)
                for name, resource in self.resource_manager.resources.items():
                    self.ai_manager.register_resource(name, resource)
            elif key == "social_manager":
                self.social_manager = SocialManager.deserialize(deepcopy(manager_data))
                self.social_manager.scheduler = self.scheduler
            elif key == "population_manager":
                self._restore_manager_scalars(self.population_manager, manager_data)
                population = self.resource_manager.resource("Population")
                if population is not None:
                    self.population_manager.population = population
            elif key == "power_grid":
                self._restore_manager_scalars(self.power_grid, manager_data)
                power = self.resource_manager.resource("Power")
                if power is not None:
                    self.power_grid.power_resource = power
                self.power_grid.producers = [self.buildings_by_id[i] for i in manager_data.get("producers", ()) if i in self.buildings_by_id]
                self.power_grid.consumers = [self.buildings_by_id[i] for i in manager_data.get("consumers", ()) if i in self.buildings_by_id]
                self.power_grid.batteries = [self.buildings_by_id[i] for i in manager_data.get("batteries", ()) if i in self.buildings_by_id]
            elif key == "construction_manager":
                manager = getattr(self, key)
                self._restore_manager_scalars(manager, manager_data)
                manager.construction_queue = deque(self._load_construction(p) for p in manager_data.get("construction_queue", ()))
                manager.active_projects = [self._load_construction(p) for p in manager_data.get("active_projects", ())]
            elif key == "research_manager":
                manager = self.research_manager
                self._restore_manager_scalars(manager, manager_data)
                manager.research_queue = deque(self._load_research(p) for p in manager_data.get("research_queue", ()))
                manager.active_projects = [self._load_research(p) for p in manager_data.get("active_projects", ())]
                manager.completed_projects = [self._load_research(p) for p in manager_data.get("completed_projects", ())]
            elif key == "maintenance_manager":
                manager = self.maintenance_manager
                self._restore_manager_scalars(manager, manager_data)
                manager.maintenance_queue.clear()
                for request in manager_data.get("maintenance_queue", ()):
                    building = self.buildings_by_id.get(request["building_id"])
                    if building is not None:
                        manager.maintenance_queue.append(MaintenanceRequest(
                            building, request.get("priority", 1), request.get("repair_amount", 10.0),
                            self.agents_by_id.get(request.get("assigned_agent")), request.get("completed", False)))
            elif key == "logistics_manager":
                manager = self.logistics_manager
                self._restore_manager_scalars(manager, manager_data)
                manager.delivery_queue.clear()
                for request in manager_data.get("delivery_queue", ()):
                    manager.delivery_queue.append(TransportRequest(
                        request["resource"], request["amount"], self._resolve_entity(request.get("source")),
                        self._resolve_entity(request.get("destination")), request.get("priority", 1),
                        self.agents_by_id.get(request.get("assigned_robot")), request.get("completed", False),
                        request.get("request_id", str(uuid4())), request.get("loading_progress", 0.0),
                        request.get("travel_progress", 0.0), request.get("unloading_progress", 0.0),
                        request.get("failed", False)))
            elif key == "emergency_manager":
                manager = self.emergency_manager
                self._restore_manager_scalars(manager, manager_data)
                manager.emergency_queue = deque(self._load_emergency(e) for e in manager_data.get("emergency_queue", ()))
                manager.active_emergencies = [self._load_emergency(e) for e in manager_data.get("active_emergencies", ())]
            else:
                self._restore_manager_scalars(getattr(self, key), manager_data)

    def _resolve_entity(self, reference):
        if not isinstance(reference, dict):
            return reference
        if "agent" in reference or "$agent" in reference:
            return self.agents_by_id.get(reference.get("agent", reference.get("$agent")))
        if "building" in reference or "$building" in reference:
            return self.buildings_by_id.get(reference.get("building", reference.get("$building")))
        return None

    def _load_construction(self, values):
        return ConstructionProject(building_name=values["building_name"],
            position=tuple(values["position"]), required_resources=dict(values.get("required_resources", {})),
            progress=values.get("progress", 0.0), priority=values.get("priority", 1),
            assigned_agent=self.agents_by_id.get(values.get("assigned_agent")),
            completed=values.get("completed", False), task_id=values.get("task_id"),
            footprint=tuple(values.get("footprint", (1, 1))))

    def _load_research(self, values):
        return ResearchProject(values["name"], values.get("description", ""),
            values.get("required_points", 0.0), values.get("progress", 0.0),
            values.get("priority", 1), self.agents_by_id.get(values.get("assigned_scientist")),
            values.get("completed", False), values.get("unlocked", False),
            values.get("category", "General"), tuple(values.get("prerequisites", ())))

    def _load_emergency(self, values):
        return Emergency(values["title"], values.get("description", ""),
            EmergencySeverity(values.get("severity", EmergencySeverity.LOW.value)),
            self._resolve_entity(values.get("source")), self._resolve_entity(values.get("target")),
            tuple(values["location"]) if values.get("location") is not None else None,
            self.agents_by_id.get(values.get("assigned_agent")), values.get("resolved", False))

    @staticmethod
    def _restore_manager_scalars(manager: Any, values: dict) -> None:
        for attr, value in values.items():
            if isinstance(manager, PowerGrid) and attr == "power_resource":
                continue
            current = getattr(manager, attr, None)
            if isinstance(current, Enum) and isinstance(value, str):
                try:
                    setattr(manager, attr, type(current)(value))
                except ValueError:
                    continue
            elif isinstance(value, (str, int, float, bool, type(None))) and not isinstance(current, (dict, list, set)):
                setattr(manager, attr, value)

    @staticmethod
    def _manager_names() -> tuple[str, ...]:
        return ("event_manager", "accident_manager", "failure_manager", "random_event_manager",
                "power_grid", "resource_manager", "population_manager", "construction_manager",
                "logistics_manager", "research_manager", "economy_manager", "emergency_manager",
                "maintenance_manager", "ai_manager", "autonomy_manager", "social_manager", "task_manager")

    @staticmethod
    def _saved_class(path: str):
        module_name, class_name = path.rsplit(".", 1)
        if not module_name.startswith("colony."):
            raise ValueError(f"Unsupported saved entity class: {path}")
        return getattr(importlib.import_module(module_name), class_name)

    # ========================================================
    # Representation
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "ColonyModel("
            f"managers={self.manager_count}, "
            f"initialized={self.initialized}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

HabrynModel = ColonyModel
