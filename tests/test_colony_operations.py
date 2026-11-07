import json
import os
from dataclasses import replace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from colony.agents.astronaut import Astronaut
from colony.agents.engineer import Engineer
from colony.agents.robot import Robot
from colony.buildings.base_building import BaseBuilding
from colony.buildings.mine import Mine
from colony.buildings.launch_pad import LaunchPad
from colony.buildings.reactor import Reactor
from colony.buildings.water_plant import WaterPlant
from colony.buildings.oxygen_generator import OxygenGenerator
from colony.environment.terrain import PLAINS
from colony.events.base_event import BaseEvent
from colony.events.accidents import Accident
from colony.events.failures import Failure
from colony.systems.emergency_manager import EmergencySeverity
from colony.initialization import ColonyConfig
from colony.simulation import Simulation
from colony.tasks.task import BaseTask, TaskStatus
from colony.visualization.renderer import Renderer
from colony.visualization.pixel_art import building_sprite, character_sprite, terrain_tile
from colony.visualization.building_visuals import BUILDING_VISUALS, building_visual
from colony.visualization.render_settings import DISPLAY_PRESETS, QUALITY_PRESETS, DisplaySettings
from colony.visualization.app import HabrynApp


def test_seeded_initial_colony_and_empty_world_configuration():
    config = ColonyConfig(seed=831)
    first = Simulation(config=config)
    second = Simulation(config=config)
    assert first.model.mars_map.width == 50
    assert len(first.model.agents_by_id) == config.astronauts + config.robots
    assert isinstance(first.model.agents_by_id[1], Engineer)
    assert any(isinstance(a, Robot) for a in first.model.agents_by_id.values())
    assert len(first.model.buildings_by_id) >= 6
    assert first.model.mars_map.statistics()["agents"] == len(first.model.agents_by_id)
    assert first.model.mars_map.statistics()["buildings"] >= len(first.model.buildings_by_id)
    assert [(p, t.terrain.name, dict(t.resource_deposit)) for p, t in first.model.mars_map.tiles.items()] == [
        (p, t.terrain.name, dict(t.resource_deposit)) for p, t in second.model.mars_map.tiles.items()]

    empty = Simulation(config=ColonyConfig(populate=False, seed=831))
    assert not empty.model.agents_by_id
    assert not empty.model.buildings_by_id
    assert empty.model.resource_manager.resource("Water") is not None


def test_facilities_and_agent_needs_use_shared_resource_inventories():
    simulation = Simulation()
    model = simulation.model
    habitat = next(b for b in model.buildings_by_id.values() if type(b).__name__ == "Habitat")
    assert habitat.oxygen is model.resource_manager.resource("Oxygen")
    assert habitat.water is model.resource_manager.resource("Water")
    assert habitat.food is model.resource_manager.resource("Food")
    before = model.resource_manager.resource_summary()
    simulation.start()
    for _ in range(simulation.scheduler.ticks_per_hour):
        simulation.step()
    after = model.resource_manager.resource_summary()
    assert after["Oxygen"] > before["Oxygen"]
    assert after["Water"] > before["Water"]
    assert after["Food"] > before["Food"]
    assert after["Fuel"] < before["Fuel"]
    assert model.resource_manager.resource("Oxygen").total_consumed > 0


def test_greenhouse_crop_stages_and_photosynthetic_oxygen_use_shared_stores():
    model = Simulation(config=ColonyConfig(seed=782)).model
    greenhouse = next(building for building in model.buildings_by_id.values()
                      if type(building).__name__ == "Greenhouse")
    oxygen = model.resource_manager.resource("Oxygen")
    assert greenhouse.oxygen is oxygen
    assert greenhouse.crop_stage == "Mature"
    food_before = model.resource_manager.amount("Food")
    oxygen_before = oxygen.current_amount

    produced = greenhouse.grow_food()
    assert produced > 0
    assert greenhouse.crop_stage == "Seedling"
    assert model.resource_manager.amount("Food") == pytest.approx(food_before + produced)
    assert oxygen.current_amount == pytest.approx(
        oxygen_before + produced * greenhouse.photosynthesis_oxygen_ratio)
    for expected_stage in ("Vegetative", "Flowering", "Mature"):
        assert greenhouse.grow_food() == 0
        assert greenhouse.crop_stage == expected_stage
    assert greenhouse.grow_food() > 0
    assert greenhouse.crop_cycles_completed == 2


def test_fuel_harvest_cargo_delivery_and_reactor_use_one_inventory_across_save_load():
    simulation = Simulation(config=ColonyConfig(
        seed=777, astronauts=1, robots=0, starting_fuel=0,
        profession_distribution=(("Engineer", 1),)))
    model = simulation.model
    detached_reactor = Reactor()
    assert detached_reactor.fuel is None
    assert detached_reactor.generate_power() == 0
    engineer = next(iter(model.agents_by_id.values()))
    reactor = next(building for building in model.buildings_by_id.values()
                   if type(building).__name__ == "Reactor")
    storage = next(building for building in model.buildings_by_id.values()
                   if type(building).__name__ == "FuelDepot")
    fuel = model.resource_manager.resource("Fuel")
    launch_site = LaunchPad(building_id=99, position=(0, 0))
    assert launch_site.fuel is None
    for y in range(3):
        for x in range(3):
            model.mars_map.set_terrain(x, y, PLAINS)
    assert model.place_building(launch_site)
    assert reactor.fuel is storage.fuel is launch_site.fuel is fuel
    with pytest.raises(RuntimeError, match="shared colony inventory"):
        reactor.refuel(5)
    assert fuel.current_amount == 0
    reactor.disable()
    assert storage.operational

    for tile in model.mars_map.tiles.values():
        tile.resource_deposit.pop("Fuel", None)
    entry = model._building_entry(storage, storage.position)
    candidates = [position for position, tile in model.mars_map.tiles.items()
                  if tile.walkable and not tile.agents and tile.building is None
                  and abs(position[0] - storage.position[0]) + abs(position[1] - storage.position[1]) >= 7
                  and model._path_for(tuple(engineer.position), position)
                  and model._path_for(position, entry)]
    source = min(candidates, key=lambda point: (abs(point[0] - storage.position[0])
                                                + abs(point[1] - storage.position[1]), point[1], point[0]))
    model.mars_map.add_resource(*source, "Fuel", 5)
    model.mars_map.explore(*source)
    model.register_visible_deposits()
    initial_position = tuple(engineer.position)
    initial_storage = fuel.current_amount
    engineer.work_schedule.update({"sleep_hour": 22, "wake_hour": 0,
                                   "work_start": 0, "work_end": 23})
    simulation.start()
    task = None
    for _ in range(1000):
        simulation.step()
        candidates = (*model.task_manager.tasks, *model.task_manager.active_tasks())
        task = next((candidate for candidate in candidates
                     if candidate.metadata.get("action") == "fuel_harvest"), None)
        if task is not None and task.metadata.get("phase") == "deliver" and engineer.has_item("Fuel", 5):
            break
    assert task is not None and task.assigned_agent is engineer
    assert task.metadata["phase"] == "deliver"
    assert model.mars_map.resource_amount(*source, "Fuel") == 0
    assert engineer.has_item("Fuel", 5)
    transit = model.world_snapshot().telemetry["fuel_logistics"]
    assert transit["in_transit"] == 5
    assert transit["active_tasks"][0]["phase"] == "deliver"
    manifest = model.logistics_manager.delivery_queue[0]
    assert manifest.amount == 5
    assert manifest.loading_progress == 100
    assert manifest.assigned_robot is engineer
    carried_from = tuple(engineer.position)
    assert carried_from != initial_position or engineer.distance_travelled > 0

    restored = Simulation.deserialize(simulation.serialize())
    model = restored.model
    engineer = model.agents_by_id[engineer.unique_id]
    task = engineer.current_task
    reactor = next(building for building in model.buildings_by_id.values()
                   if type(building).__name__ == "Reactor")
    storage = next(building for building in model.buildings_by_id.values()
                   if type(building).__name__ == "FuelDepot")
    launch_site = next(building for building in model.buildings_by_id.values()
                       if type(building).__name__ == "LaunchPad")
    fuel = model.resource_manager.resource("Fuel")
    assert task is not None and task.metadata["phase"] == "deliver"
    assert engineer.has_item("Fuel", 5)
    position_before_delivery = tuple(engineer.position)
    for _ in range(100):
        model.step_agents_and_tasks()
        if task.status == TaskStatus.COMPLETED:
            break
    assert task.status == TaskStatus.COMPLETED
    assert tuple(engineer.position) != position_before_delivery
    assert not engineer.has_item("Fuel", 1)
    assert fuel.current_amount == pytest.approx(initial_storage + 5)
    assert storage.fuel is reactor.fuel is launch_site.fuel is fuel
    assert task.metadata["transfer_event"]["quantity"] == 5
    assert task.metadata["transfer_event"]["source"]["position"] == list(source)
    assert task.metadata["transfer_event"]["destination"] == {
        "type": "FuelDepot", "building_id": storage.building_id}
    assert model.resource_manager.transfer_history["Fuel"] == 5
    manifest = next(item for item in model.logistics_manager.delivery_queue
                    if item.request_id == task.metadata["logistics_request_id"])
    assert manifest.completed
    assert manifest.travel_progress == 100
    assert manifest.unloading_progress == 100
    assert model.logistics_manager.completed_deliveries == 1

    reactor.enable()
    before_reactor_use = fuel.current_amount
    assert reactor.generate_power() > 0
    assert fuel.current_amount == pytest.approx(before_reactor_use - reactor.fuel_consumption)
    assert model.world_snapshot().telemetry["fuel_logistics"]["consumed_total"] == pytest.approx(
        reactor.fuel_consumption)


def test_standard_building_footprint_is_shared_by_map_and_construction():
    simulation = Simulation(config=ColonyConfig(seed=778))
    model = simulation.model
    for building in model.buildings_by_id.values():
        occupied = [tile for tile in model.mars_map.tiles.values() if tile.building is building]
        assert type(building).default_footprint == (3, 3)
        assert len(occupied) == 9
        assert max(tile.local_x for tile in occupied) == 2
        assert max(tile.local_y for tile in occupied) == 2
        assert model._building_entry(building) is not None
    assert any(type(building).__name__ == "SolarArray" for building in model.power_grid.producers)
    assert model.population_manager.total_population == 6
    sites = [(x, y) for y in range(model.mars_map.height - 2)
             for x in range(model.mars_map.width - 5)
             if all((tile := model.mars_map.get_tile(x + dx, y + dy)) is not None
                    and tile.terrain.buildable and not tile.occupied and not tile.agents
                    for dy in range(3) for dx in range(6))]
    x, y = sites[0]
    project = model.queue_construction("SolarArray", (x, y))
    assert project.footprint == (3, 3)
    with pytest.raises(ValueError, match="reserves"):
        model.queue_construction("SolarArray", (x + 2, y))


def test_specialized_storage_uses_finite_shared_resource_inventories():
    model = Simulation(config=ColonyConfig(seed=781)).model
    facilities = {type(building).__name__: building for building in model.buildings_by_id.values()}
    policies = {"FuelDepot": ("Fuel", "fuel"), "WaterReservoir": ("Water", "water"),
                "FoodWarehouse": ("Food", "food"),
                "OxygenStorageFacility": ("Oxygen", "oxygen"),
                "MaterialsWarehouse": ("Minerals", "minerals")}
    for facility_name, (resource_name, attribute) in policies.items():
        facility = facilities[facility_name]
        resource = model.resource_manager.resource(resource_name)
        assert getattr(facility, attribute) is resource
        assert facility.accepts_resource(resource_name)
        assert resource.storage_capacity > 0
        assert resource.current_amount <= resource.storage_capacity
    fuel_depot = facilities["FuelDepot"]
    water_reservoir = facilities["WaterReservoir"]
    fuel_deposit = next((position for position, tile in model.mars_map.tiles.items()
                         if tile.resource_deposit.get("Fuel", 0) > 0), None)
    if fuel_deposit is not None:
        with pytest.raises(ValueError, match="does not accept Fuel"):
            model.create_fuel_harvest_task(fuel_deposit, 1, water_reservoir)
    assert not fuel_depot.accepts_resource("Food")


def test_initial_exploration_and_rover_survey_are_seeded_and_persisted():
    simulation = Simulation(config=ColonyConfig(seed=779, astronauts=1, robots=1))
    model = simulation.model
    explored_before = len(model.mars_map.explored_tiles())
    assert explored_before == round(model.mars_map.width * model.mars_map.height * .40)
    rover = next(agent for agent in model.agents_by_id.values()
                 if isinstance(agent, Robot))
    assert rover.role == "exploration"
    assert rover.tools == ["camera", "spectrometer"]

    model.ai_manager.assess_and_plan(model)
    task = next(task for task in model.task_manager.tasks if task.metadata.get("action") == "explore")
    assert task.metadata["required_role"] == "exploration"
    battery_before = rover.battery_level
    simulation.start()
    for _ in range(80):
        simulation.step()
        if model.exploration_reports:
            break
    assert model.exploration_reports
    assert rover.battery_level < battery_before
    assert len(model.mars_map.explored_tiles()) > explored_before
    assert rover.position == tuple(model.exploration_reports[-1]["position"])

    restored = Simulation.deserialize(simulation.serialize())
    restored_rover = restored.model.agents_by_id[rover.unique_id]
    assert restored_rover.role == "exploration"
    assert restored_rover.battery_level == pytest.approx(rover.battery_level)
    assert restored.model.exploration_reports == model.exploration_reports
    assert restored.model.discovered_deposits == model.discovered_deposits


def test_stranded_rover_requires_engineer_and_finite_power_recovery():
    simulation = Simulation(config=ColonyConfig(
        seed=780, astronauts=1, robots=1,
        profession_distribution=(("Engineer", 1),)))
    model = simulation.model
    engineer = next(agent for agent in model.agents_by_id.values() if hasattr(agent, "suit_oxygen"))
    rover = next(agent for agent in model.agents_by_id.values() if isinstance(agent, Robot))
    rover.battery_level = 0
    rover.position = tuple(rover.position)
    power_before = model.resource_manager.amount("Power")

    for _ in range(40):
        model.step_agents_and_tasks()
        if rover.battery_level > 0:
            break

    assert 20 <= rover.battery_level <= 25
    assert model.resource_manager.amount("Power") == pytest.approx(power_before - 10)
    recovery = next(task for task in model.task_manager.completed_tasks
                    if task.metadata.get("action") == "recover_rover")
    assert recovery.target is rover
    assert recovery.assigned_agent is engineer
    assert recovery.metadata["power_consumed"] == 10
    assert engineer.distance_travelled > 0


def test_lighting_and_solar_cycle_tracks_one_martian_sol_per_scheduler_day():
    simulation = Simulation(config=ColonyConfig(seed=13))
    simulation.start()
    for _ in range(simulation.scheduler.ticks_per_hour * simulation.scheduler.hours_per_day):
        simulation.step()
    assert simulation.scheduler.sol == 2
    assert simulation.model.day_night.minute == 0
    assert simulation.model.day_night.fractional_minute == 0
    restored = Simulation.deserialize(simulation.serialize())
    assert restored.model.day_night.serialize() == simulation.model.day_night.serialize()


def test_dust_weather_reduces_solar_output_and_eva_uses_tile_radiation():
    simulation = Simulation(config=ColonyConfig(seed=6, radiation_severity=2.0))
    model = simulation.model
    solar = next(building for building in model.buildings_by_id.values()
                 if type(building).__name__ == "SolarArray")
    model.day_night.minute = 720
    model.day_night._update()
    model.weather.weather = type(model.weather.weather).DUST_STORM
    dust_before = solar.dust_penalty
    model.hourly_update()
    assert solar.dust_penalty > dust_before
    assert solar.sunlight_efficiency == pytest.approx(.3 * model.day_night.solar_efficiency)
    astronaut = model.agents_by_id[1]
    astronaut.outside = True
    tile = model.mars_map.get_tile(*astronaut.position)
    tile.radiation = .5
    radiation_before = astronaut.radiation
    model.hourly_update()
    assert astronaut.radiation > radiation_before + .5


def test_task_assignment_movement_and_execution_use_existing_task_api():
    simulation = Simulation(config=ColonyConfig(populate=False, seed=7))
    model = simulation.model
    model.mars_map.set_terrain(2, 2, PLAINS)
    model.mars_map.set_terrain(3, 2, PLAINS)
    agent = Astronaut(unique_id=77, name="Pathfinder", profession="Astronaut", position=(2, 2))
    agent.work_schedule.update({"work_start": 0, "work_end": 23, "sleep_hour": 22, "wake_hour": 0})
    model.register_agent(agent)
    task = BaseTask(name="Inspect sample", duration=2, location=(3, 2))
    model.task_manager.register_task(task)
    simulation.start()
    for _ in range(4):
        simulation.step()
    assert agent.position == (3, 2)
    assert task.status == TaskStatus.COMPLETED
    assert agent.tasks_completed == 1


def test_shortages_are_reported_and_affect_agent_needs():
    simulation = Simulation(config=ColonyConfig(populate=False, seed=3))
    model = simulation.model
    model.mars_map.set_terrain(2, 2, PLAINS)
    agent = Astronaut(unique_id=9, name="Test Crew", profession="Astronaut", position=(2, 2))
    model.register_agent(agent)
    for name in ("Oxygen", "Water", "Food"):
        resource = model.resource_manager.resource(name)
        resource.consume(resource.current_amount)
    simulation.start()
    for _ in range(simulation.scheduler.ticks_per_hour):
        simulation.step()
    assert {"Oxygen", "Water", "Food"} <= model.resource_manager.shortages
    assert agent.hunger > 0
    assert agent.thirst > 0
    assert agent.oxygen < 100


def test_stored_power_dispatch_keeps_facilities_online_for_the_hour():
    model = Simulation(config=ColonyConfig(populate=False)).model
    power = model.resource_manager.resource("Power")
    power.consume(power.current_amount - 10)
    facility = BaseBuilding(building_id=33, name="Critical Lab", position=(2, 2))
    facility.power_required = 10
    model.power_grid.register_consumer(facility)
    model.power_grid.hourly_update()
    assert power.current_amount == 0
    assert facility.is_powered
    assert model.power_grid.unmet_demand == 0


def test_json_save_load_restores_inventories_relationships_events_and_continues(tmp_path):
    simulation = Simulation()
    model = simulation.model
    simulation.start()
    for _ in range(simulation.scheduler.ticks_per_hour):
        simulation.step()
    model.event_manager.publish(BaseEvent(name="Solar inspection", description="Routine system notice",
                                          source=model.agents_by_id[1], target=model.buildings_by_id[2]))
    agent = model.agents_by_id[1]
    task = BaseTask(name="Inspect habitat", duration=4, location=agent.position)
    model.task_manager.register_task(task)
    assert model.task_manager.assign_task(agent, task)
    task.start()
    task.advance(25.0)
    before = model.resource_manager.resource_summary()
    save_path = tmp_path / "habryn.json"
    simulation.save(save_path)
    save_data = json.loads(save_path.read_text(encoding="utf-8"))
    restored = Simulation.load(save_path)
    restored_model = restored.model
    assert restored.current_tick == simulation.current_tick
    assert restored_model.resource_manager.resource_summary() == before
    assert restored_model.population_manager.population is restored_model.resource_manager.resource("Population")
    assert restored_model.power_grid.power_resource is restored_model.resource_manager.resource("Power")
    assert restored_model.buildings_by_id[1].oxygen is restored_model.resource_manager.resource("Oxygen")
    assert restored_model.mars_map.statistics()["occupied_tiles"] == model.mars_map.statistics()["occupied_tiles"]
    assert len(restored_model.event_manager.active_events) == 1
    assert restored_model.event_manager.active_events[0].source is restored_model.agents_by_id[1]
    assert restored_model.event_manager.active_events[0].target is restored_model.buildings_by_id[2]
    restored_task = next(t for t in restored_model.task_manager.tasks if t.name == "Inspect habitat")
    assert restored_model.agents_by_id[1].current_task is restored_task
    assert restored_task.assigned_agent is restored_model.agents_by_id[1]
    assert restored_task.progress == 25.0
    restored.start()
    restored.step()
    assert restored.current_tick == simulation.current_tick + 1
    assert save_data["model"]["managers"]["resource_manager"]["resources"]["Water"]["data"]["storage"]


def test_renderer_snapshot_includes_current_needs_and_building_status_without_mutation():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    simulation = Simulation()
    snapshot = simulation.world_snapshot()
    tick = simulation.current_tick
    renderer = Renderer(screen)
    renderer.draw(snapshot, pygame.Rect(0, 0, 600, 400))
    assert "hunger" in snapshot.agents[0]
    assert "integrity" in snapshot.buildings[0]
    assert "resource_inventory" in snapshot.telemetry
    assert simulation.current_tick == tick
    pygame.quit()


def test_pixel_tiles_are_seeded_cached_and_building_footprints_pick_as_one_entity():
    first = terrain_tile("Plains", 3, 8, 42, True)
    assert first is terrain_tile("Plains", 3, 8, 42, True)
    assert pygame.image.tostring(first, "RGB") != pygame.image.tostring(
        terrain_tile("Plains", 3, 9, 42, True), "RGB")
    assert pygame.image.tostring(character_sprite(False, 0, 0, False), "RGBA") != pygame.image.tostring(
        character_sprite(False, 0, 2, False), "RGBA")
    building_kinds = ("Habitat", "SolarArray", "Reactor", "Greenhouse", "OxygenGenerator",
                      "WaterPlant", "Battery", "Workshop", "Mine", "StorageFacility",
                      "MedicalBay", "RecyclingPlant", "LaunchPad", "Laboratory",
                      "CommunicationsCenter")
    sprites = [pygame.image.tostring(building_sprite(kind, 32, 32, True, False), "RGBA")
               for kind in building_kinds]
    assert len(set(sprites)) == len(building_kinds)
    simulation = Simulation()
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    renderer = Renderer(screen, seed=simulation.config.seed)
    viewport = pygame.Rect(18, 62, 700, 600)
    building = next(b for b in simulation.world_snapshot().buildings if b["footprint"][0] > 1)
    bx, by = building["position"]
    for zoom in (.55, 1.25, 2.5):
        renderer.camera.zoom = zoom
        renderer.camera.x, renderer.camera.y = bx, by
        pos = (viewport.x + int(1.5 * renderer.camera.cell * renderer.pixel_scale),
               viewport.y + int(.5 * renderer.camera.cell * renderer.pixel_scale))
        picked = renderer.pick(simulation.world_snapshot(), pos, viewport)
        assert picked[0] == "building"
        assert picked[1]["id"] == building["id"]
    snapshot = simulation.world_snapshot()
    for agent in snapshot.agents:
        ax, ay = agent["position"]
        renderer.camera.x, renderer.camera.y = ax, ay
        center = (viewport.x + int(.5 * renderer.camera.cell * renderer.pixel_scale),
                  viewport.y + int(.5 * renderer.camera.cell * renderer.pixel_scale))
        selected = renderer.pick(snapshot, center, viewport)
        assert selected[0] == "agent"
        assert selected[1]["id"] == agent["id"]
    renderer.draw(simulation.world_snapshot(), viewport)
    assert renderer.last_world_surface_size == viewport.size
    assert renderer.last_draw_stats["temporary_world_surfaces"] == 0
    pygame.quit()


def test_gui_layout_controls_and_rendering_do_not_tick_unprompted():
    pygame.init()
    simulation = Simulation()
    app = HabrynApp(simulation, size=(1024, 700))
    try:
        before = simulation.current_tick
        snapshot, viewport = app._draw()
        assert simulation.current_tick == before
        assert app.buttons["map"].right <= app.screen.get_width()
        assert viewport.right < app.screen.get_width()
        resize = pygame.event.Event(pygame.VIDEORESIZE, size=(1180, 760), w=1180, h=760)
        app.handle_event(resize, snapshot, viewport)
        app._draw()
        assert app.screen.get_size() == (1180, 760)
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        assert app.paused
        assert app.advance_frame(.25) == 0
        assert simulation.current_tick == before
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_PERIOD))
        assert simulation.current_tick == before + 1
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        assert not app.paused
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        assert app.paused
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g))
        assert app.renderer.show_grid
        before_speed = simulation.simulation_speed
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_PLUS))
        assert simulation.simulation_speed > before_speed
        old_camera = (app.camera.x, app.camera.y, app.camera.zoom)
        app.camera.zoom_at(1.2, (300, 200), app.renderer.pixel_scale)
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(100, 200), button=1))
        app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(120, 210), rel=(20, 10), buttons=(1, 0, 0)))
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(120, 210), button=1))
        assert (app.camera.x, app.camera.y, app.camera.zoom) != old_camera
        app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=(960, 640), w=960, h=640))
        _width, _height, _side, narrow_view, narrow_panel = app._layout()
        assert narrow_panel.right == 960
        assert narrow_view.right == narrow_panel.left
        assert app._fit("A VERY LONG FACILITY NAME", 100, app.small_font).endswith("…")
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b))
        app._draw()
        assert app.build_mode and "SolarArray" in app.build_palette
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        assert not app.build_mode and app.running
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                           pos=app.buttons["research"].center, button=1))
        research_snapshot, research_viewport = app._draw()
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                           pos=app.research_buttons["Solar Efficiency"].center, button=1),
                         research_snapshot, research_viewport)
        assert app.simulation.model.research_manager.research_queue[0].name == "Solar Efficiency"
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=app.buttons["new"].center, button=1))
        scenario_snapshot, scenario_viewport = app._draw()
        assert app.scenario_mode and "First Landing" in app.scenario_buttons
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                           pos=app.scenario_buttons["First Landing"].center, button=1),
                         scenario_snapshot, scenario_viewport)
        assert app.simulation.config.scenario_name == "First Landing"
        assert app.simulation.config.astronauts == 3
        assert not app.scenario_mode
    finally:
        app.simulation.stop()
        pygame.quit()


def test_character_identity_is_seeded_persistent_and_uses_detailed_sprite_frames():
    first = Simulation(config=ColonyConfig(seed=91))
    second = Simulation(config=ColonyConfig(seed=91))
    human_a, human_b = first.model.agents_by_id[1], second.model.agents_by_id[1]
    assert human_a.appearance == human_b.appearance
    assert human_a.personality == human_b.personality
    assert character_sprite(False, 0, 0, False, human_a.appearance).get_size() == (48, 64)
    robot = next(agent for agent in first.model.agents_by_id.values() if isinstance(agent, Robot))
    assert character_sprite(True, 0, 0, False, robot.appearance).get_size() == (64, 56)
    assert len({tuple(agent.appearance["suit_color"]) for agent in first.model.agents_by_id.values()
                if not isinstance(agent, Robot)}) > 1
    restored = Simulation.deserialize(first.serialize())
    assert restored.model.agents_by_id[1].appearance == human_a.appearance
    assert character_sprite(False, 0, 0, False, restored.model.agents_by_id[1].appearance) is character_sprite(
        False, 0, 0, False, human_a.appearance)


def test_scenario_presets_are_distinct_and_arrivals_respect_housing():
    research = Simulation(config=ColonyConfig.preset("Research Outpost", seed=5))
    industrial = Simulation(config=ColonyConfig.preset("Industrial Base", seed=5))
    assert any(type(building).__name__ == "Laboratory" for building in research.model.buildings_by_id.values())
    assert any(type(building).__name__ == "Mine" for building in industrial.model.buildings_by_id.values())
    assert len(research.model.agents_by_id) != len(industrial.model.agents_by_id)
    first_landing = Simulation(config=ColonyConfig.preset("First Landing", seed=5))
    initial_count = len(first_landing.model.agents_by_id)
    first_landing.scheduler.sol = 10
    first_landing.model.daily_update()
    assert len(first_landing.model.agents_by_id) == initial_count + 3
    assert len(first_landing.model.event_manager.active_events) >= 1
    assert first_landing.model.population_manager.occupied_housing <= first_landing.model.population_manager.housing_capacity
    first_landing.model.daily_update()
    assert len(first_landing.model.agents_by_id) == initial_count + 3


def test_all_six_scenario_modes_keep_their_identity_and_initial_conditions():
    expected = {
        "First Landing": (3, 1, 450, "Normal", 160, 220, 130, ()),
        "Research Outpost": (7, 3, 1000, "Normal", 600, 750, 400,
                             ("Laboratory", "CommunicationsCenter", "MedicalBay")),
        "Industrial Base": (8, 6, 1000, "Normal", 600, 750, 400,
                            ("Mine", "Workshop", "RecyclingPlant")),
        "Survival": (4, 2, 250, "Survival", 49.5, 71.5, 38.5, ()),
        "Sandbox": (6, 3, 1000, "Sandbox", 1200, 1500, 800, ()),
        "Established Settlement": (12, 5, 2000, "Normal", 1200, 1500, 900,
                                   ("Laboratory", "Workshop", "MedicalBay")),
    }
    for name, (astronauts, robots, power, difficulty, water, oxygen, food, extra_buildings) in expected.items():
        simulation = Simulation(config=ColonyConfig.preset(name, seed=31))
        assert simulation.config.scenario_name == name
        assert (simulation.config.astronauts, simulation.config.robots) == (astronauts, robots)
        assert simulation.config.starting_power == power
        assert simulation.config.difficulty == difficulty
        assert simulation.config.seed == 31
        assert len(simulation.model.agents_by_id) == astronauts + robots
        assert simulation.model.initialized
        assert simulation.model.resource_manager.amount("Water") == pytest.approx(water)
        assert simulation.model.resource_manager.amount("Oxygen") == pytest.approx(oxygen)
        assert simulation.model.resource_manager.amount("Food") == pytest.approx(food)
        building_types = {type(building).__name__ for building in simulation.model.buildings_by_id.values()}
        assert set(extra_buildings) <= building_types
    app = HabrynApp(Simulation(config=ColonyConfig.preset("Sandbox", seed=31)), size=(960, 640))
    try:
        app.scenario_mode = True
        app._draw()
        assert set(app.scenario_buttons) == set(expected)
        for size in ((1280, 800), (960, 640), (1920, 1080)):
            app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=size, w=size[0], h=size[1]))
            assert app.renderer.screen is app.screen
            app.scenario_mode = True
            app._draw()
            app.scenario_mode = False
            app.crew_mode = True
            app._draw()
            app.crew_mode = False
            app.research_mode = True
            app._draw()
            app.research_mode = False
    finally:
        app.simulation.stop()
        pygame.quit()


def test_building_visual_catalogue_covers_initial_colony_with_distinct_sprites():
    simulation = Simulation(config=ColonyConfig(seed=11))
    kinds = {building["category"] for building in simulation.world_snapshot().buildings}
    assert kinds <= BUILDING_VISUALS.keys()
    sprites = [building_sprite(kind, 48, 48, True, False) for kind in kinds]
    fingerprints = {pygame.image.tostring(sprite, "RGBA") for sprite in sprites}
    assert len(fingerprints) >= len(kinds) - 1
    assert building_visual("FuelDepot")["primary"] == "amber"
    assert building_visual("WaterReservoir")["primary"] == "blue"


def test_scenario_configuration_changes_real_map_inventory_and_runtime():
    config = ColonyConfig(width=30, height=30, seed=19, settlement_position=(15, 15),
        terrain_distribution=(("Plains", 1.0),), initial_buildings=("Habitat", "Laboratory"),
        astronauts=1, robots=0, deposit_abundance=2.0, production_modifier=1.5,
        needs_intensity=0.0, event_frequency=0.0, simulation_speed=2.0,
        colony_name="Ares Station", colony_id="ARES-01")
    simulation = Simulation(config=config)
    model = simulation.model
    assert model.colony_name == "Ares Station" and model.colony_id == "ARES-01"
    assert simulation.simulation_speed == 2.0
    assert {tile.terrain.name for tile in model.mars_map.tiles.values()} == {"Plains"}
    assert set(type(building).__name__ for building in model.buildings_by_id.values()) == {"Habitat", "Laboratory"}
    solar_config = Simulation(config=ColonyConfig(seed=19, production_modifier=1.5))
    solar = next(building for building in solar_config.model.buildings_by_id.values()
                 if type(building).__name__ == "SolarArray")
    assert solar.power_output == 90.0
    assert model.mars_map.get_tile(9, 13).resource_deposit["Water"] == 2800.0
    assert model.needs_intensity == 0.0
    assert model.accident_manager.accident_rate == 0


def test_runtime_autonomy_and_social_intensity_settings_are_authoritative():
    simulation = Simulation(config=ColonyConfig(seed=8, autonomy_enabled=False, social_intensity=0))
    assert not simulation.model.autonomy_manager.enabled
    assert simulation.model.social_manager.intensity == 0
    agent = next(agent for agent in simulation.model.agents_by_id.values() if hasattr(agent, "suit_oxygen"))
    simulation.start()
    simulation.step()
    assert agent.current_activity == "Autonomy disabled"
    assert not simulation.model.social_manager.conversations


def test_save_load_deterministic_continuation_including_social_state():
    simulation = Simulation(config=ColonyConfig(seed=123))
    model = simulation.model
    crew = [agent for agent in model.agents_by_id.values() if hasattr(agent, "suit_oxygen")]
    model.mars_map.set_terrain(10, 10, PLAINS)
    model.mars_map.set_terrain(11, 10, PLAINS)
    assert model.move_agent(crew[0], (10, 10))
    assert model.move_agent(crew[1], (11, 10))
    crew[0].social_need = crew[1].social_need = 100
    for agent in crew[:2]:
        agent.work_schedule.update({"sleep_hour": 0, "wake_hour": 0,
                                    "work_start": 0, "work_end": 23})
    simulation.start()
    for _ in range(simulation.scheduler.ticks_per_hour):
        simulation.step()
    assert model.social_manager.conversations
    saved = simulation.serialize()
    for _ in range(120):
        simulation.step()
    expected = simulation.serialize()
    restored = Simulation.deserialize(saved)
    for _ in range(120):
        restored.step()
    actual = restored.serialize()
    if actual != expected:
        differences = []

        def collect(left, right, path="state"):
            if len(differences) >= 20:
                return
            if isinstance(left, dict) and isinstance(right, dict):
                for key in sorted(left.keys() | right.keys(), key=str):
                    if key not in left or key not in right:
                        differences.append(f"{path}.{key}: missing on one side")
                    else:
                        collect(left[key], right[key], f"{path}.{key}")
            elif isinstance(left, list) and isinstance(right, list):
                if len(left) != len(right):
                    differences.append(f"{path}: lengths {len(left)} != {len(right)}")
                for index, (first, second) in enumerate(zip(left, right)):
                    collect(first, second, f"{path}[{index}]")
            elif left != right:
                differences.append(f"{path}: {left!r} != {right!r}")

        collect(expected, actual)
        pytest.fail("save/load continuation diverged: " + "; ".join(differences))


def test_accident_and_failure_systems_register_entities_and_restore_event_links():
    simulation = Simulation()
    model = simulation.model
    astronaut = model.agents_by_id[1]
    robot = next(agent for agent in model.agents_by_id.values() if isinstance(agent, Robot))
    building = model.buildings_by_id[1]
    assert astronaut in model.accident_manager.astronauts
    assert robot in model.accident_manager.robots
    assert building in model.failure_manager.buildings
    accident = model.accident_manager.create_accident(astronaut)
    failure = model.failure_manager.create_failure(building)
    assert astronaut.health < 100
    assert building.integrity < 100
    model.event_manager.publish(accident)
    model.event_manager.publish(failure)
    restored = Simulation.deserialize(json.loads(json.dumps(simulation.serialize()))).model
    assert restored.accident_manager.astronauts[0] is restored.agents_by_id[1]
    assert restored.accident_manager.robots[0].unique_id == robot.unique_id
    assert restored.failure_manager.buildings[0] is restored.buildings_by_id[1]
    assert isinstance(restored.accident_manager.accidents[0], Accident)
    assert isinstance(restored.failure_manager.failures[0], Failure)
    assert restored.accident_manager.accidents[0] is restored.event_manager.active_events[0]
    assert restored.accident_manager.accidents[0].victim is restored.agents_by_id[1]
    assert restored.failure_manager.failures[0].building is restored.buildings_by_id[1]
    assert all(item.target is not None for item in restored.emergency_manager.emergency_queue)


def test_engineer_resolves_critical_facility_failure_emergency():
    simulation = Simulation(config=ColonyConfig(seed=14))
    model = simulation.model
    building = model.buildings_by_id[1]
    building.damage(60)
    building.emergency_shutdown = True
    building.set_power(False)
    emergency = model.emergency_manager.report_emergency(
        "Critical habitat failure", "Restore structural integrity and reopen the facility.",
        EmergencySeverity.CRITICAL, source=building, target=building, location=building.position)
    engineer = next(agent for agent in model.agents_by_id.values() if type(agent).__name__ == "Engineer")
    engineer.work_schedule.update({"work_start": 0, "work_end": 23, "sleep_hour": 22, "wake_hour": 0})
    simulation.start()
    for _ in range(40):
        simulation.step()
    assert emergency.assigned_agent is engineer
    assert emergency.resolved
    assert building.integrity == building.max_integrity
    assert not building.emergency_shutdown


def test_research_requires_scientist_and_lab_then_changes_power_generation():
    simulation = Simulation(config=ColonyConfig.preset("Research Outpost", seed=37))
    model = simulation.model
    solar = next(building for building in model.buildings_by_id.values()
                 if type(building).__name__ == "SolarArray")
    starting_output = solar.power_output
    project = model.research_manager.create_project("Solar Efficiency", "Operational research test", 30)
    simulation.start()
    for _ in range(600):
        simulation.step()
    assert project.completed
    assert project.assigned_scientist is not None
    assert project.assigned_scientist.experience > 0
    assert solar.power_output == starting_output * 1.15
    restored = Simulation.deserialize(simulation.serialize()).model
    restored_solar = next(building for building in restored.buildings_by_id.values()
                          if type(building).__name__ == "SolarArray")
    assert restored_solar.power_output == solar.power_output
    assert restored.research_manager.completed_projects[0].completed


def test_research_tree_enforces_prerequisites_and_persists_branch_metadata():
    simulation = Simulation(config=ColonyConfig.preset("Research Outpost", seed=42))
    manager = simulation.model.research_manager
    with pytest.raises(ValueError, match="Solar Efficiency"):
        manager.create_project("Crop Yield", "Agriculture branch", 140)
    root = manager.create_project("Solar Efficiency", "Energy branch", 160)
    assert root.category == "Energy" and root.prerequisites == ()
    manager.complete_project(root)
    child = manager.create_project("Crop Yield", "Agriculture branch", 140)
    assert child.category == "Agriculture"
    assert child.prerequisites == ("Solar Efficiency",)
    restored = Simulation.deserialize(simulation.serialize()).model.research_manager
    assert restored.research_queue[0].category == "Agriculture"
    assert restored.research_queue[0].prerequisites == ("Solar Efficiency",)


def test_construction_uses_validated_footprints_resources_tasks_and_save_load():
    simulation = Simulation(config=ColonyConfig(seed=29))
    model = simulation.model
    engineer = next(agent for agent in model.agents_by_id.values() if type(agent).__name__ == "Engineer")
    candidates = []
    for y in range(max(1, engineer.position[1] - 4), min(model.mars_map.height - 1, engineer.position[1] + 4)):
        for x in range(max(1, engineer.position[0] - 4), min(model.mars_map.width - 1, engineer.position[0] + 4)):
            tiles = [model.mars_map.get_tile(x + dx, y + dy) for dy in range(3) for dx in range(3)]
            if all(tile and not tile.occupied and not tile.agents for tile in tiles):
                candidates.append((abs(x - engineer.position[0]) + abs(y - engineer.position[1]), x, y))
    _, x, y = min(candidates)
    for dy in range(3):
        for dx in range(3):
            model.mars_map.set_terrain(x + dx, y + dy, PLAINS)
    project = model.queue_construction("SolarArray", (x, y), {"Minerals": 60})
    with pytest.raises(ValueError, match="reserves"):
        model.queue_construction("SolarArray", (x, y))
    engineer.work_schedule.update({"work_start": 0, "work_end": 23, "sleep_hour": 22, "wake_hour": 0})
    minerals_before = model.resource_manager.amount("Minerals")
    consumed_before = model.resource_manager.consumption_history.get("Minerals", 0.0)
    simulation.start()
    for _ in range(8):
        simulation.step()
    assert project.task_id is not None
    assert project.progress > 0
    assert minerals_before - model.resource_manager.amount("Minerals") == 60
    assert model.resource_manager.consumption_history["Minerals"] - consumed_before == 60
    restored = Simulation.deserialize(simulation.serialize())
    for _ in range(80):
        restored.step()
    restored_project = restored.model.construction_manager.active_projects[0] if restored.model.construction_manager.active_projects else None
    solar_arrays = [building for building in restored.model.buildings_by_id.values()
                    if type(building).__name__ == "SolarArray" and building.position == (x, y)]
    assert solar_arrays
    assert restored.model.mars_map.statistics()["occupied_tiles"] >= 9
    assert restored.model.resource_manager.amount("Minerals") < minerals_before
    assert restored.model.construction_manager.completed_projects == 1
    assert restored_project is None


def test_large_colony_character_rendering_at_50_crew_20_robots():
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    simulation = Simulation(config=ColonyConfig(width=50, height=50, seed=17,
                                                astronauts=50, robots=20))
    assert sum(hasattr(agent, "suit_oxygen") for agent in simulation.model.agents_by_id.values()) == 50
    assert sum(isinstance(agent, Robot) for agent in simulation.model.agents_by_id.values()) == 20
    renderer = Renderer(screen, seed=17)
    viewport = pygame.Rect(0, 62, 680, 620)
    renderer.draw(simulation.world_snapshot(), viewport)
    assert renderer.last_world_surface_size == viewport.size
    idle = character_sprite(False, 0, 0, False, simulation.model.agents_by_id[1].appearance, "idle")
    working = character_sprite(False, 0, 0, True, simulation.model.agents_by_id[1].appearance, "working")
    walking = character_sprite(False, 1, 1, False, simulation.model.agents_by_id[1].appearance, "walking")
    assert pygame.image.tostring(idle, "RGBA") != pygame.image.tostring(working, "RGBA")
    assert pygame.image.tostring(idle, "RGBA") != pygame.image.tostring(walking, "RGBA")
    pygame.quit()


def test_200_square_world_can_place_100_crew_and_40_robots():
    simulation = Simulation(config=ColonyConfig(width=200, height=200, seed=20261107,
                                                astronauts=100, robots=40))
    model = simulation.model
    assert len(model.mars_map.tiles) == 40_000
    assert sum(hasattr(agent, "suit_oxygen") for agent in model.agents_by_id.values()) == 100
    assert sum(isinstance(agent, Robot) for agent in model.agents_by_id.values()) == 40
    assert model.mars_map.statistics()["agents"] == 140
    agent = model.agents_by_id[1]
    destination = (2, 2)
    path = model._path_for(tuple(agent.position), destination)
    assert path
    assert path[-1] == destination


def test_seeded_terrain_uses_coherent_regions_and_resource_belts():
    model = Simulation(config=ColonyConfig(width=100, height=100, seed=202)).model
    same_neighbors = 0
    neighbor_pairs = 0
    for (x, y), tile in model.mars_map.tiles.items():
        assert tile.region != "Unknown"
        for neighbor_position in ((x + 1, y), (x, y + 1)):
            neighbor = model.mars_map.get_tile(*neighbor_position)
            if neighbor is not None:
                neighbor_pairs += 1
                same_neighbors += tile.terrain.name == neighbor.terrain.name
    assert same_neighbors / neighbor_pairs > 0.4
    assert any(tile.terrain.name == "Ice" and tile.resource_deposit.get("Water", 0) > 0
               for tile in model.mars_map.tiles.values())
    assert any(tile.terrain.name == "Rock" and tile.resource_deposit.get("Minerals", 0) > 0
               for tile in model.mars_map.tiles.values())


def test_ai_forecasts_resource_shortage_and_persists_explainable_goal():
    simulation = Simulation(config=ColonyConfig(seed=77))
    model = simulation.model
    assert model.resource_manager.consume("Water", 200)
    model.ai_manager.assess_and_plan(model)
    assert model.resource_manager.consume("Water", 100)
    model.scheduler.tick += model.scheduler.ticks_per_hour
    model.ai_manager.assess_and_plan(model)

    forecast = model.ai_manager.resource_forecasts["Water"]
    assert forecast["net_change_per_hour"] == -100
    assert forecast["hours_until_empty"] == 3
    goal = next(goal for goal in model.ai_manager.goals if goal["id"] == "reserve:Water")
    assert goal["severity"] == "critical"
    assert goal["status"] == "planned"
    assert any(project.building_name == "WaterPlant"
               for project in model.construction_manager.construction_queue)
    assert "run out in 3.0 h" in goal["reason"]
    assert "queued WaterPlant" in goal["reason"]
    restored = Simulation.deserialize(simulation.serialize())
    assert restored.model.ai_manager.resource_forecasts == model.ai_manager.resource_forecasts
    assert restored.model.ai_manager.goals == model.ai_manager.goals
    assert restored.model.ai_manager.decisions == model.ai_manager.decisions
    simulation.start()
    for _ in range(120):
        simulation.step()
    assert sum(type(building).__name__ == "WaterPlant"
               for building in model.buildings_by_id.values()) == 2
    assert not model.construction_manager.construction_queue


def test_farmer_physically_tends_greenhouse_and_pays_water_cost():
    simulation = Simulation(config=ColonyConfig(seed=91))
    model = simulation.model
    farmer = next(agent for agent in model.agents_by_id.values()
                  if hasattr(agent, "assign_greenhouse"))
    greenhouse = next(building for building in model.buildings_by_id.values()
                      if type(building).__name__ == "Greenhouse")
    greenhouse.crop_health = 55
    farmer.work_schedule.update({"sleep_hour": 0, "wake_hour": 0,
                                 "work_start": 0, "work_end": 23})
    model.ai_manager.assess_and_plan(model)
    before_position = tuple(farmer.position)
    before_water = model.resource_manager.amount("Water")
    for _ in range(100):
        simulation.step_once()
        if greenhouse.crop_health > 55:
            break

    assert tuple(farmer.position) != before_position
    assert greenhouse.crop_health == 60
    assert model.resource_manager.amount("Water") == pytest.approx(before_water - 2)
    assert farmer.current_task is None
    assert any(item["decision"].startswith("Recover Greenhouse")
               for item in model.ai_manager.decisions)


def test_ai_maintenance_request_becomes_engineer_work_and_is_completed():
    simulation = Simulation(config=ColonyConfig(seed=114))
    model = simulation.model
    engineer = next(agent for agent in model.agents_by_id.values()
                    if agent.profession == "Engineer")
    building = next(building for building in model.buildings_by_id.values()
                    if type(building).__name__ == "SolarArray")
    building.maintenance = 25
    request = model.maintenance_manager.request_maintenance(building, priority=4)
    duplicate = model.maintenance_manager.request_maintenance(building, priority=2)
    assert duplicate is request
    assert len(model.maintenance_manager.pending_requests()) == 1
    engineer.work_schedule.update({"sleep_hour": 0, "wake_hour": 0,
                                   "work_start": 0, "work_end": 23})
    model.ai_manager.assess_and_plan(model)
    assert any(task.metadata.get("action") == "maintenance" for task in model.task_manager.tasks)

    simulation.start()
    for _ in range(100):
        simulation.step()
        if request.completed:
            break

    assert request.completed
    assert building.maintenance > 25
    assert building.repairs_received == 1
    assert not model.maintenance_manager.pending_requests()
    assert engineer.current_task is None


def test_mine_extracts_only_finite_map_deposits():
    simulation = Simulation(config=ColonyConfig(populate=False, seed=31))
    model = simulation.model
    mine = Mine(building_id=1, position=(20, 20))
    assert model.place_building(mine)
    model.resource_manager.resource("Population").generate(6)
    for tile in model.mars_map.tiles.values():
        tile.resource_deposit.pop("Minerals", None)
    model.mars_map.add_resource(21, 20, "Minerals", 12)
    before = model.resource_manager.amount("Minerals")

    extracted = model._operate_mine(mine)
    assert extracted == pytest.approx(12)
    assert model.mars_map.resource_amount(21, 20, "Minerals") == 0
    assert model.resource_manager.amount("Minerals") == pytest.approx(before + 12)
    assert model._operate_mine(mine) == 0
    assert model.resource_manager.amount("Minerals") == pytest.approx(before + 12)


def test_water_processing_depletes_mapped_ice_and_oxygen_consumes_water():
    simulation = Simulation(config=ColonyConfig(populate=False, seed=32))
    model = simulation.model
    plant = WaterPlant(building_id=1, position=(20, 20))
    oxygen_generator = OxygenGenerator(building_id=2, position=(23, 20))
    assert model.place_building(plant)
    assert model.place_building(oxygen_generator)
    for tile in model.mars_map.tiles.values():
        tile.resource_deposit.pop("Water", None)
    model.mars_map.add_resource(20, 23, "Water", 15)
    water_before = model.resource_manager.amount("Water")

    assert model._operate_water_plant(plant) == pytest.approx(15)
    assert model.mars_map.resource_amount(20, 23, "Water") == 0
    assert model.resource_manager.amount("Water") == pytest.approx(water_before + 15)
    assert model._operate_water_plant(plant) == 0

    oxygen_before = model.resource_manager.amount("Oxygen")
    water_before = model.resource_manager.amount("Water")
    power_before = model.resource_manager.amount("Power")
    generated = oxygen_generator.generate_oxygen()
    assert generated == pytest.approx(25)
    assert model.resource_manager.amount("Oxygen") == pytest.approx(oxygen_before + 25)
    assert model.resource_manager.amount("Water") == pytest.approx(
        water_before - 25 * oxygen_generator.water_per_oxygen)
    assert model.resource_manager.amount("Power") < power_before

    model.resource_manager.consume("Water", model.resource_manager.amount("Water") - 1)
    power_before = model.resource_manager.amount("Power")
    assert oxygen_generator.generate_oxygen() == 0
    assert model.resource_manager.amount("Power") == pytest.approx(power_before)


def test_native_resolution_quality_presets_and_zoom_anchor_are_presentation_only():
    pygame.init()
    point = (713, 421)
    camera = Renderer(pygame.Surface((1920, 1080))).camera
    camera.x, camera.y = 7.25, 9.5
    before = camera.screen_to_world(point)
    camera.zoom_at(1.7, point)
    assert camera.screen_to_world(point) == pytest.approx(before)
    assert camera.world_to_screen(before) == pytest.approx(point)

    for name, expected in (("1080p", (1920, 1080)), ("1440p", (2560, 1440)), ("4k", (3840, 2160))):
        settings = DisplaySettings.for_preset(name)
        assert (settings.width, settings.height) == expected == DISPLAY_PRESETS[name]
    assert set(QUALITY_PRESETS) == {"Performance", "Balanced", "High", "Ultra"}
    terrain_low = terrain_tile("Sand", 91, 4, 27, True, False, 32, 1)
    terrain_high = terrain_tile("Sand", 91, 4, 27, True, False, 96, 4)
    assert terrain_low.get_size() == (32, 32)
    assert terrain_high.get_size() == (96, 96)
    assert pygame.image.tostring(terrain_low, "RGB") != pygame.image.tostring(terrain_high, "RGB")
    astronaut = character_sprite(False, 2, 1, True, {}, "working", detail=3)
    rover = character_sprite(True, 1, 2, False, {"carrying_load": True}, "walking", detail=3)
    assert astronaut.get_size() == (144, 192)
    assert rover.get_size() == (192, 168)
    pygame.quit()


def test_renderer_quality_changes_clear_art_caches_without_simulation_changes():
    pygame.init()
    simulation = Simulation(config=ColonyConfig(seed=712))
    screen = pygame.Surface((1280, 800))
    renderer = Renderer(screen, seed=712, quality="Balanced")
    viewport = pygame.Rect(0, 0, 1280, 800)
    snapshot = simulation.world_snapshot()
    renderer.draw(snapshot, viewport)
    assert renderer.last_draw_stats["temporary_world_surfaces"] == 0
    before_tick = simulation.current_tick
    before_state = simulation.serialize()
    assert renderer._scaled_tiles
    renderer.set_quality("Ultra")
    assert not renderer._scaled_tiles and not renderer._scaled_people and not renderer._scaled_buildings
    renderer.draw(snapshot, viewport)
    assert renderer.last_world_surface_size == viewport.size
    assert simulation.current_tick == before_tick
    assert simulation.serialize() == before_state
    with pytest.raises(ValueError, match="Unknown rendering quality"):
        renderer.set_quality("Maximum")
    pygame.quit()


def test_screen_resolution_resize_keeps_world_picking_and_minimap_in_sync():
    pygame.init()
    app = HabrynApp(size=(1920, 1080), quality="Performance")
    try:
        for size in ((1920, 1080), (2560, 1440), (3840, 2160)):
            app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=size, w=size[0], h=size[1]))
            assert app.ui_scale == app._display_dpi_scale(size)
            assert app.renderer.ui_scale == app.ui_scale
            snapshot, viewport = app._draw()
            building = next(item for item in snapshot.buildings if item["category"] == "Habitat")
            bx, by = building["position"]
            app.camera.zoom = .9
            app.camera.x, app.camera.y = bx, by
            point = (viewport.x + round(.5 * app.camera.cell),
                     viewport.y + round(.5 * app.camera.cell))
            picked = app.renderer.pick(snapshot, point, viewport)
            assert picked[0] == "building" and picked[1]["id"] == building["id"]
            minimap = app.renderer.minimap_rect(viewport)
            assert minimap is not None
            before = (app.camera.x, app.camera.y)
            assert app.renderer.center_from_minimap(snapshot, minimap.center, viewport)
            assert (app.camera.x, app.camera.y) != before
            assert app.renderer.last_world_surface_size == viewport.size
        app.set_ui_scale(1.4)
        assert app.ui_scale == app.renderer.ui_scale == 1.4
        assert app.small_font.get_height() >= round(12 * 1.4)
        app.set_quality("High")
        assert app.renderer.quality == "High"
        with pytest.raises(ValueError, match="UI scale"):
            app.set_ui_scale(3.1)
    finally:
        app.simulation.stop()
        pygame.quit()


def test_selected_object_summary_stays_pinned_and_readable_while_sidebar_scrolls():
    pygame.init()
    app = HabrynApp(size=(1280, 800), quality="Performance")
    try:
        snapshot, _viewport = app._draw()
        building = next(item for item in snapshot.buildings if item["category"] == "FuelDepot")
        app._select(("building", building))
        panel = app._layout()[-1]
        app.panel_scroll = 0
        app._draw_sidebar(panel, snapshot)
        first_rect = app.selected_card_rect.copy()
        assert first_rect.top >= panel.top
        assert first_rect.bottom < panel.bottom
        assert first_rect.width == panel.width - app.u(16)

        app.panel_scroll = 10_000
        app._draw_sidebar(panel, snapshot)
        assert app.selected_card_rect == first_rect
        assert app.panel_scroll <= max(0, app.panel_content_height -
                                      (panel.height - (first_rect.height + app.u(20))) + app.u(12))
    finally:
        app.simulation.stop()
        pygame.quit()


def test_minimap_surface_is_cached_until_simulation_state_or_ui_scale_changes():
    pygame.init()
    simulation = Simulation(config=ColonyConfig(seed=719))
    screen = pygame.Surface((1280, 800))
    renderer = Renderer(screen, seed=719, quality="Performance")
    viewport = pygame.Rect(0, 0, 960, 800)
    try:
        snapshot = simulation.world_snapshot()
        renderer.draw(snapshot, viewport)
        renderer.draw(snapshot, viewport)
        assert renderer.minimap_rebuild_count == 1

        renderer.draw(replace(snapshot, tick=snapshot.tick + 1), viewport)
        assert renderer.minimap_rebuild_count == 2

        renderer.set_ui_scale(1.25)
        renderer.draw(simulation.world_snapshot(), viewport)
        assert renderer.minimap_rebuild_count == 3
    finally:
        simulation.stop()
        pygame.quit()


def test_fullscreen_toggle_restores_windowed_dimensions_and_camera(monkeypatch):
    pygame.init()
    app = HabrynApp(size=(1000, 700), quality="Performance")
    try:
        app._layout()
        app.camera.center_on((18.5, 23.25), app.last_viewport.size)
        expected_center = app._camera_center()
        requested_modes = []

        def fake_set_mode(size, flags=0):
            requested_modes.append((size, flags))
            result_size = (1280, 720) if flags & pygame.FULLSCREEN else size
            return pygame.Surface(result_size)

        monkeypatch.setattr(pygame.display, "set_mode", fake_set_mode)
        app.toggle_fullscreen()
        assert app.fullscreen
        assert requested_modes[-1] == (app._desktop_size(), pygame.FULLSCREEN)
        assert app._camera_center() == pytest.approx(expected_center)

        app.toggle_fullscreen()
        assert not app.fullscreen
        assert requested_modes[-1][0] == (1000, 700)
        assert app.screen.get_size() == (1000, 700)
        assert app._camera_center() == pytest.approx(expected_center)
    finally:
        app.simulation.stop()
        pygame.quit()


def test_monitor_dpi_change_rebuilds_ui_scale_and_preserves_camera(monkeypatch):
    pygame.init()
    app = HabrynApp(size=(1280, 800), quality="Performance")
    try:
        app._layout()
        app.camera.center_on((21.5, 17.25), app.last_viewport.size)
        center = app._camera_center()
        monkeypatch.setattr(app, "_display_dpi_scale", lambda _size: 1.5)
        event = pygame.event.Event(pygame.WINDOWDISPLAYCHANGED)
        app.handle_event(event)
        assert app.ui_scale == app.renderer.ui_scale == 1.5
        assert app._camera_center() == pytest.approx(center)
    finally:
        app.simulation.stop()
        pygame.quit()


def test_paused_static_frame_skips_redundant_screen_redraws():
    pygame.init()
    app = HabrynApp(size=(1280, 800), quality="Performance")
    try:
        app._toggle_pause()
        app._draw()
        before = app.paused_redraw_skips
        app._draw()
        assert app.paused_redraw_skips == before + 1

        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g))
        app._draw()
        after_redraw = app.paused_redraw_skips
        app._draw()
        assert app.paused_redraw_skips == after_redraw + 1
    finally:
        app.simulation.stop()
        pygame.quit()
