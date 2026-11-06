import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from colony.agents.astronaut import Astronaut
from colony.agents.engineer import Engineer
from colony.agents.robot import Robot
from colony.buildings.base_building import BaseBuilding
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
    assert model.power_grid.total_generation > 0
    assert model.population_manager.total_population == 6


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
    assert renderer.last_world_surface_size == (viewport.width // 2, viewport.height // 2)
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
        app.screen = pygame.display.set_mode((960, 640), pygame.RESIZABLE)
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
    assert actual == expected


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


def test_construction_uses_validated_footprints_resources_tasks_and_save_load():
    simulation = Simulation(config=ColonyConfig(seed=29))
    model = simulation.model
    engineer = next(agent for agent in model.agents_by_id.values() if type(agent).__name__ == "Engineer")
    candidates = []
    for y in range(max(1, engineer.position[1] - 4), min(model.mars_map.height - 1, engineer.position[1] + 4)):
        for x in range(max(1, engineer.position[0] - 4), min(model.mars_map.width - 1, engineer.position[0] + 4)):
            tiles = [model.mars_map.get_tile(x + dx, y + dy) for dy in range(2) for dx in range(2)]
            if all(tile and not tile.occupied and not tile.agents for tile in tiles):
                candidates.append((abs(x - engineer.position[0]) + abs(y - engineer.position[1]), x, y))
    _, x, y = min(candidates)
    for dy in range(2):
        for dx in range(2):
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
    assert restored.model.mars_map.statistics()["occupied_tiles"] >= 4
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
    assert renderer.last_world_surface_size == (viewport.width // 2, viewport.height // 2)
    idle = character_sprite(False, 0, 0, False, simulation.model.agents_by_id[1].appearance, "idle")
    working = character_sprite(False, 0, 0, True, simulation.model.agents_by_id[1].appearance, "working")
    walking = character_sprite(False, 1, 1, False, simulation.model.agents_by_id[1].appearance, "walking")
    assert pygame.image.tostring(idle, "RGBA") != pygame.image.tostring(working, "RGBA")
    assert pygame.image.tostring(idle, "RGBA") != pygame.image.tostring(walking, "RGBA")
    pygame.quit()
