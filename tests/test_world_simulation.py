import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from colony.agents.base_agent import BaseAgent
from colony.buildings.base_building import BaseBuilding
from colony.simulation import Simulation
from colony.initialization import ColonyConfig
from colony.environment.terrain import PLAINS
from colony.visualization.renderer import Camera, Renderer


def empty_simulation():
    return Simulation(config=ColonyConfig(populate=False))


def test_entity_registry_and_spatial_consistency():
    sim = empty_simulation()
    model = sim.model
    for position in ((2, 3), (4, 3)):
        model.mars_map.set_terrain(*position, PLAINS)
    agent = BaseAgent(unique_id=7, name="Ada", profession="Scientist", position=(2, 3))
    model.register_agent(agent)
    assert model.mars_map.get_tile(2, 3).agents == [agent]
    assert model.move_agent(7, (4, 3))
    assert model.mars_map.get_tile(2, 3).agents == []
    assert model.mars_map.get_tile(4, 3).agents == [agent]
    assert model.remove_agent(7) is agent
    assert not model.agents_by_id


def test_multitile_building_registered_once_and_removed():
    model = empty_simulation().model
    for y in (5, 6):
        for x in (5, 6):
            model.mars_map.set_terrain(x, y, PLAINS)
    building = BaseBuilding(building_id=2, name="Habitat", position=(5, 5))
    assert model.place_building(building, 2, 2)
    snap = model.world_snapshot()
    assert len(snap.buildings) == 1
    assert snap.buildings[0]["footprint"] == (2, 2)
    assert model.mars_map.statistics()["occupied_tiles"] == 4
    assert model.remove_building(2) is building
    assert model.mars_map.statistics()["occupied_tiles"] == 0


def test_invalid_and_duplicate_registration():
    model = empty_simulation().model
    agent = BaseAgent(unique_id=1, name="A", profession="Engineer", position=(1000, 0))
    with pytest.raises(ValueError):
        model.register_agent(agent)
    model.mars_map.set_terrain(0, 0, PLAINS)
    agent.position = (0, 0)
    model.register_agent(agent)
    with pytest.raises(ValueError):
        model.register_agent(agent)


def test_ticks_pause_step_and_deserialization_scheduler_link():
    sim = empty_simulation()
    sim.start()
    sim.step()
    assert sim.current_tick == 1
    sim.pause()
    sim.step()
    assert sim.current_tick == 1
    sim.step_once()
    assert sim.current_tick == 2
    restored = Simulation.deserialize(sim.serialize())
    assert restored.model.scheduler is restored.scheduler
    restored.start()
    restored.step()
    assert restored.current_tick == 3


def test_entity_round_trip_preserves_footprint():
    sim = empty_simulation()
    sim.model.mars_map.set_terrain(1, 1, PLAINS)
    sim.model.register_agent(BaseAgent(unique_id=11, name="Lin", profession="Medic", position=(1, 1)))
    for y in (3, 4):
        for x in (3, 4):
            sim.model.mars_map.set_terrain(x, y, PLAINS)
    sim.model.place_building(BaseBuilding(building_id=12, name="Habitat", position=(3, 3)), 2, 2)
    restored = Simulation.deserialize(sim.serialize())
    assert list(restored.model.agents_by_id) == [11]
    assert restored.model.mars_map.get_tile(1, 1).agents[0].name == "Lin"
    assert restored.model.world_snapshot().buildings[0]["footprint"] == (2, 2)


def test_camera_transform_and_render_do_not_tick():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    camera = Camera()
    point = (4.5, 8.25)
    assert camera.screen_to_world(camera.world_to_screen(point)) == pytest.approx(point)
    camera.zoom_at(1.5, (200, 160))
    sim = Simulation()
    before = sim.current_tick
    Renderer(screen, camera).draw(sim.world_snapshot(), pygame.Rect(0, 0, 500, 480))
    assert sim.current_tick == before
    pygame.quit()
