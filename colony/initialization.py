"""Reproducible initial colony setup using Habryn's existing entities."""
from __future__ import annotations

from dataclasses import dataclass
import random

from colony.agents.astronaut import Astronaut
from colony.agents.engineer import Engineer
from colony.agents.farmer import Farmer
from colony.agents.medic import Medic
from colony.agents.robot import Robot
from colony.agents.scientist import Scientist
from colony.buildings.battery import Battery
from colony.buildings.greenhouse import Greenhouse
from colony.buildings.habitat import Habitat
from colony.buildings.oxygen_generator import OxygenGenerator
from colony.buildings.reactor import Reactor
from colony.buildings.solar_array import SolarArray
from colony.buildings.water_plant import WaterPlant
from colony.buildings.laboratory import Laboratory
from colony.buildings.medical_bay import MedicalBay
from colony.buildings.mine import Mine
from colony.buildings.recycling_plant import RecyclingPlant
from colony.buildings.storage_facility import StorageFacility
from colony.buildings.fuel_depot import FuelDepot
from colony.buildings.water_reservoir import WaterReservoir
from colony.buildings.food_warehouse import FoodWarehouse
from colony.buildings.oxygen_storage_facility import OxygenStorageFacility
from colony.buildings.materials_warehouse import MaterialsWarehouse
from colony.buildings.workshop import Workshop
from colony.buildings.communications_center import CommunicationsCenter
from colony.environment.terrain import PLAINS, ROCK, SAND, ICE, CRATER
from colony.environment.terrain import get_terrain
from colony.resources.food import Food
from colony.resources.fuel import Fuel
from colony.resources.heat import Heat
from colony.resources.minerals import Minerals
from colony.resources.morale import Morale
from colony.resources.oxygen import Oxygen
from colony.resources.population import Population
from colony.resources.power import Power
from colony.resources.science_points import SciencePoints
from colony.resources.waste import Waste
from colony.resources.water import Water


@dataclass(frozen=True)
class ColonyConfig:
    width: int = 50
    height: int = 50
    seed: int | None = 42
    populate: bool = True
    astronauts: int = 6
    robots: int = 3
    starting_power: float = 1000.0
    starting_water: float = 600.0
    starting_oxygen: float = 750.0
    starting_food: float = 400.0
    starting_minerals: float = 250.0
    starting_fuel: float = 300.0
    starting_science: float = 0.0
    colony_name: str = "Habryn"
    colony_id: str = "COLONY-07"
    scenario_name: str = "Established Settlement"
    difficulty: str = "Normal"
    social_intensity: float = 1.0
    autonomy_enabled: bool = True
    profession_distribution: tuple[tuple[str, int], ...] = ()
    scheduled_arrivals: tuple[tuple[int, int, int], ...] = ()
    settlement_position: tuple[int, int] | None = None
    terrain_distribution: tuple[tuple[str, float], ...] = ()
    initial_buildings: tuple[str, ...] | None = None
    deposit_abundance: float = 1.0
    production_modifier: float = 1.0
    needs_intensity: float = 1.0
    event_frequency: float = 1.0
    radiation_severity: float = 1.0
    dust_storm_frequency: float = 1.0
    simulation_speed: float = 1.0

    def __post_init__(self):
        if self.width < 12 or self.height < 12:
            raise ValueError("Colony maps must be at least 12 by 12 tiles")
        if min(self.astronauts, self.robots) < 0:
            raise ValueError("Initial population counts cannot be negative")
        if self.difficulty not in {"Sandbox", "Easy", "Normal", "Hard", "Survival", "Custom"}:
            raise ValueError("Difficulty must be Sandbox, Easy, Normal, Hard, Survival, or Custom")
        if not 0.0 <= self.social_intensity <= 2.0:
            raise ValueError("Social intensity must be between 0 and 2")
        if any(sol < 1 or humans < 0 or robots < 0 for sol, humans, robots in self.scheduled_arrivals):
            raise ValueError("Arrivals require a positive sol and non-negative crew counts")
        if self.settlement_position is not None:
            x, y = self.settlement_position
            if not 5 <= x < self.width - 5 or not 5 <= y < self.height - 5:
                raise ValueError("Settlement position must leave five tiles of map margin")
        for value, label in ((self.deposit_abundance, "deposit abundance"),
                             (self.production_modifier, "production modifier"),
                             (self.needs_intensity, "needs intensity"),
                             (self.event_frequency, "event frequency"),
                             (self.radiation_severity, "radiation severity"),
                             (self.dust_storm_frequency, "dust storm frequency"),
                             (self.simulation_speed, "simulation speed")):
            if value < 0 or value > 10:
                raise ValueError(f"{label} must be between 0 and 10")
        if self.simulation_speed == 0:
            raise ValueError("Simulation speed must be positive")
        if any(weight <= 0 for _name, weight in self.terrain_distribution):
            raise ValueError("Terrain distribution weights must be positive")
        if self.initial_buildings is not None and len(set(self.initial_buildings)) != len(self.initial_buildings):
            raise ValueError("Initial building selections cannot contain duplicates")
        try:
            for name, _weight in self.terrain_distribution:
                get_terrain(name)
        except KeyError as error:
            raise ValueError(f"Unknown terrain in distribution: {error.args[0]}") from error

    @classmethod
    def preset(cls, name: str, seed: int | None = 42) -> "ColonyConfig":
        presets = {
            "First Landing": dict(astronauts=3, robots=1, starting_power=450, starting_water=160,
                starting_oxygen=220, starting_food=130, starting_minerals=80, starting_fuel=100,
                scheduled_arrivals=((10, 2, 1),)),
            "Research Outpost": dict(astronauts=7, robots=3, starting_science=200,
                profession_distribution=(("Scientist", 3), ("Engineer", 2), ("Medic", 1), ("Farmer", 1))),
            "Industrial Base": dict(astronauts=8, robots=6, starting_minerals=900, starting_fuel=700,
                deposit_abundance=1.5, production_modifier=1.2,
                profession_distribution=(("Engineer", 3), ("Robotics", 2), ("Farmer", 1), ("Medic", 1), ("Scientist", 1))),
            "Survival": dict(astronauts=4, robots=2, starting_power=250, starting_water=90,
                starting_oxygen=130, starting_food=70, starting_minerals=60, starting_fuel=80,
                difficulty="Survival", needs_intensity=1.25, event_frequency=2.0,
                radiation_severity=1.5, dust_storm_frequency=2.5),
            "Sandbox": dict(astronauts=6, robots=3, difficulty="Sandbox", deposit_abundance=2.0,
                event_frequency=.5, dust_storm_frequency=.5),
            "Established Settlement": dict(astronauts=12, robots=5, starting_power=2000,
                starting_water=1200, starting_oxygen=1500, starting_food=900, starting_minerals=700,
                scheduled_arrivals=((20, 4, 2),)),
        }
        if name not in presets:
            raise ValueError(f"Unknown colony scenario: {name}")
        return cls(seed=seed, scenario_name=name, **presets[name])


def initialize_colony(model, config: ColonyConfig) -> None:
    """Set up terrain, authoritative resources, facilities, and personnel."""
    rng = random.Random(config.seed)
    if config.terrain_distribution:
        terrain_types = [get_terrain(name) for name, _weight in config.terrain_distribution]
        terrain_weights = [weight for _name, weight in config.terrain_distribution]
    else:
        terrain_types, terrain_weights = (PLAINS, PLAINS, SAND, ROCK, ICE, CRATER), None
    center = config.settlement_position or (config.width // 2, config.height // 2)
    region_size = max(8, int((config.width * config.height / 36) ** 0.5))
    columns = (config.width + region_size - 1) // region_size
    rows = (config.height + region_size - 1) // region_size
    regions = []
    for row in range(rows):
        for column in range(columns):
            x = min(config.width - 1, column * region_size + region_size // 2
                    + rng.randint(-region_size // 4, region_size // 4))
            y = min(config.height - 1, row * region_size + region_size // 2
                    + rng.randint(-region_size // 4, region_size // 4))
            terrain = rng.choice(terrain_types) if terrain_weights is None else rng.choices(
                terrain_types, weights=terrain_weights, k=1)[0]
            regions.append((x, y, terrain))
    region_names = {"Plains": "Rocky Plains", "Rock": "Basalt Highlands", "Sand": "Dune Fields",
                    "Ice": "Frozen Valley", "Crater": "Crater Field", "Cliff": "Canyon Rim",
                    "Lava Tube": "Volcanic Region"}
    for tile in model.mars_map.tiles.values():
        region_id, region = min(
            enumerate(regions), key=lambda item: (tile.x - item[1][0]) ** 2 + (tile.y - item[1][1]) ** 2)
        terrain = region[2]
        tile.terrain = terrain
        tile.walkable = tile.terrain.walkable
        tile.elevation = rng.uniform(-1.5, 1.5)
        tile.radiation = rng.uniform(0.0, 0.08) * config.radiation_severity
        tile.region = f"{region_names.get(terrain.name, terrain.name)} {region_id + 1:02d}"
        if terrain.name == "Ice" and rng.random() < 0.12:
            model.mars_map.add_resource(tile.x, tile.y, "Water",
                                        rng.uniform(250.0, 900.0) * config.deposit_abundance)
        elif terrain.name == "Rock" and rng.random() < 0.10:
            model.mars_map.add_resource(tile.x, tile.y, "Minerals",
                                        rng.uniform(150.0, 650.0) * config.deposit_abundance)
    # The first settlement lies on a stable, walkable plain with nearby deposits.
    for dy in range(-10, 11):
        for dx in range(-10, 11):
            model.mars_map.set_terrain(center[0] + dx, center[1] + dy, PLAINS)
            tile = model.mars_map.get_tile(center[0] + dx, center[1] + dy)
            if tile:
                tile.explored = True
                tile.region = "Settlement"
    target_explored = round(config.width * config.height * 0.40)
    unexplored_positions = [position for position, tile in model.mars_map.tiles.items() if not tile.explored]
    additional = min(max(0, target_explored - len(model.mars_map.explored_tiles())),
                     len(unexplored_positions))
    for position in rng.sample(unexplored_positions, additional):
        model.mars_map.explore(*position)
    model.register_visible_deposits()
    for dx, dy, amount in ((-6, -2, 1400.0), (6, 2, 850.0), (0, 7, 500.0)):
        x = min(config.width - 1, max(0, center[0] + dx))
        y = min(config.height - 1, max(0, center[1] + dy))
        model.mars_map.add_resource(x, y, "Water", amount * config.deposit_abundance)
        model.mars_map.add_resource(x, y, "Minerals", amount * 1.5 * config.deposit_abundance)

    inventory_scale = {"Sandbox": 2.0, "Easy": 1.25, "Normal": 1.0,
                       "Hard": .75, "Survival": .55, "Custom": 1.0}.get(config.difficulty, 1.0)

    resources = (
        Power(current_amount=config.starting_power * inventory_scale, storage_capacity=5000.0),
        Water(current_amount=config.starting_water * inventory_scale, storage_capacity=5000.0),
        Oxygen(current_amount=config.starting_oxygen * inventory_scale, storage_capacity=5000.0),
        Food(current_amount=config.starting_food * inventory_scale, storage_capacity=3000.0),
        Minerals(current_amount=config.starting_minerals * inventory_scale, storage_capacity=10000.0),
        Fuel(current_amount=config.starting_fuel * inventory_scale, storage_capacity=3000.0),
        Heat(current_amount=100.0, storage_capacity=1000.0),
        Population(current_amount=0.0, storage_capacity=200.0),
        Waste(current_amount=0.0, storage_capacity=1000.0),
        Morale(current_amount=80.0, storage_capacity=100.0),
        SciencePoints(current_amount=config.starting_science * inventory_scale, storage_capacity=100000.0),
    )
    manager = model.resource_manager
    for resource in resources:
        manager.register_resource(resource)
        model.ai_manager.register_resource(resource.name, resource)
    model.population_manager.population = manager.resource("Population")
    model.power_grid.power_resource = manager.resource("Power")
    model.social_manager.intensity = config.social_intensity
    model.autonomy_manager.enabled = config.autonomy_enabled
    model.arrival_schedule = tuple(config.scheduled_arrivals)
    model.needs_intensity = config.needs_intensity
    model.colony_name = config.colony_name
    model.colony_id = config.colony_id
    model.radiation_severity = config.radiation_severity
    model.weather.dust_storm_frequency = config.dust_storm_frequency
    model.accident_manager.accident_rate *= config.event_frequency
    model.failure_manager.failure_rate *= config.event_frequency
    model.random_event_manager.event_rate *= config.event_frequency

    if not config.populate:
        return

    building_catalog = {
        "Habitat": Habitat, "SolarArray": SolarArray, "Reactor": Reactor,
        "OxygenGenerator": OxygenGenerator, "WaterPlant": WaterPlant,
        "Greenhouse": Greenhouse, "Battery": Battery,
        "Laboratory": Laboratory, "CommunicationsCenter": CommunicationsCenter,
        "MedicalBay": MedicalBay, "Mine": Mine, "Workshop": Workshop,
        "StorageFacility": StorageFacility, "RecyclingPlant": RecyclingPlant,
        "FuelDepot": FuelDepot, "WaterReservoir": WaterReservoir,
        "FoodWarehouse": FoodWarehouse, "OxygenStorageFacility": OxygenStorageFacility,
        "MaterialsWarehouse": MaterialsWarehouse,
    }
    scenario_names = {
        "Research Outpost": ("Laboratory", "CommunicationsCenter", "MedicalBay"),
        "Industrial Base": ("Mine", "Workshop", "RecyclingPlant"),
        "Established Settlement": ("Laboratory", "Workshop", "MedicalBay"),
    }
    names = ["Habitat", "SolarArray", "Reactor", "OxygenGenerator", "WaterPlant",
             "Greenhouse", "Battery"]
    if min(config.width, config.height) >= 16:
        names.extend(("FuelDepot", "WaterReservoir", "FoodWarehouse",
                      "OxygenStorageFacility", "MaterialsWarehouse"))
    else:
        names.append("StorageFacility")
    names.extend(scenario_names.get(config.scenario_name, ()))
    if config.initial_buildings is not None:
        names = list(config.initial_buildings)
    missing = [name for name in names if name not in building_catalog]
    if missing:
        raise ValueError(f"Unknown initial buildings: {', '.join(missing)}")
    spacing = 4 if min(config.width, config.height) >= 16 else 3
    slots = [(x, y) for y in range(0, config.height - 2, spacing)
             for x in range(0, config.width - 2, spacing)]
    slots.sort(key=lambda pos: (abs(pos[0] + 1 - center[0]) + abs(pos[1] + 1 - center[1]), pos[1], pos[0]))
    next_id = 1
    for name in names:
        building_class = building_catalog[name]
        width, height = building_class.default_footprint
        position = next((slot for slot in slots
                         if all((tile := model.mars_map.get_tile(slot[0] + dx, slot[1] + dy)) is not None
                                and tile.terrain.buildable and not tile.occupied and not tile.agents
                                for dy in range(height) for dx in range(width))), None)
        if position is None:
            raise ValueError(f"No available {width}x{height} site for initial {name}")
        building = building_class(building_id=next_id, position=position)
        next_id += 1
        slots.remove(position)
        for attribute in ("power_output", "oxygen_output", "water_output", "science_output"):
            if attribute in getattr(building, "__dataclass_fields__", {}):
                setattr(building, attribute, getattr(building, attribute) * config.production_modifier)
        if hasattr(building, "growth_bonus"):
            building.growth_bonus = min(2.0, building.growth_bonus * config.production_modifier)
        if not model.place_building(building):
            raise ValueError(f"Could not place initial {name} at {position}")

    fuel_sites = [(x, y) for (x, y), tile in model.mars_map.tiles.items()
                  if not tile.occupied and tile.terrain.buildable and tile.walkable]
    fuel_sites.sort(key=lambda pos: (abs(pos[0] - center[0]) + abs(pos[1] - center[1]), pos[1], pos[0]))
    for position in fuel_sites[-3:]:
        model.mars_map.add_resource(*position, "Fuel", 400.0 * config.deposit_abundance)

    model.register_visible_deposits()
    crew_types = (Engineer, Scientist, Farmer, Medic, Astronaut, Astronaut)
    distribution = dict(config.profession_distribution)
    if distribution:
        profession_classes = {cls.__name__: cls for cls in crew_types}
        profession_classes["Robotics"] = Engineer
        chosen = [profession_classes[name] for name, count in distribution.items()
                  for _ in range(count) if name in profession_classes]
        if chosen:
            crew_types = tuple(chosen)
    population_total = config.astronauts + config.robots
    radius = max(5, int((population_total * 2) ** 0.5) + 3)
    available = [(x, y)
                 for y in range(max(0, center[1] - radius), min(config.height, center[1] + radius + 1))
                 for x in range(max(0, center[0] - radius), min(config.width, center[0] + radius + 1))
                 if (tile := model.mars_map.get_tile(x, y)) is not None and tile.walkable
                 and not tile.occupied and tile.building is None and not tile.agents]
    if len(available) < population_total:
        nearby = set(available)
        available.extend((x, y) for (x, y), tile in model.mars_map.tiles.items()
                         if (x, y) not in nearby and tile.walkable and not tile.occupied
                         and tile.building is None and not tile.agents)
    if len(available) < population_total:
        raise ValueError(f"Map has space for only {len(available)} of {population_total} starting agents")
    rng.shuffle(available)
    for index in range(config.astronauts):
        position = next(p for p in available if model.mars_map.get_tile(*p).walkable
                        and not model.mars_map.get_tile(*p).occupied
                        and not model.mars_map.get_tile(*p).agents)
        available.remove(position)
        cls = crew_types[index % len(crew_types)]
        agent = cls(unique_id=index + 1, name=f"{cls.__name__} {index + 1}",
                    profession=cls.__name__, position=position)
        model.register_agent(agent)
    model.population_manager.update_population()
    model.population_manager.update_population()
    model.population_manager.update_housing()
    for index in range(config.robots):
        position = next(p for p in available if model.mars_map.get_tile(*p).walkable
                        and not model.mars_map.get_tile(*p).occupied
                        and not model.mars_map.get_tile(*p).agents)
        available.remove(position)
        roles = ("exploration", "mining", "cargo", "construction", "maintenance")
        role = roles[index % len(roles)]
        tools = {"exploration": ["camera", "spectrometer"], "mining": ["drill"],
                 "cargo": ["cargo_bay"], "construction": ["loader"],
                 "maintenance": ["repair_arm"]}[role]
        agent = Robot(unique_id=1001 + index, name=f"{role.replace('_', ' ').title()} Rover {index + 1}",
                      profession="Colony Robot", position=position,
                      serial_number=f"HAB-R{index + 1:03}", role=role, tools=tools)
        model.register_agent(agent)
