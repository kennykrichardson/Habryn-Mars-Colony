"""
Global configuration for the Space Colony simulation.

Every configurable value belongs here.
"""

from pathlib import Path

# ----------------------------------------------------
# Project
# ----------------------------------------------------

PROJECT_NAME = "Space Colony"

ROOT_DIR = Path(__file__).parent

SAVE_DIRECTORY = ROOT_DIR / "saves"
AUTOSAVE_DIRECTORY = SAVE_DIRECTORY / "autosave"

# ----------------------------------------------------
# Grid
# ----------------------------------------------------

GRID_WIDTH = 50
GRID_HEIGHT = 50
TORUS = False

# ----------------------------------------------------
# Time
# ----------------------------------------------------

TICKS_PER_HOUR = 60
HOURS_PER_DAY = 24

DEFAULT_SIMULATION_SPEED = 1

# ----------------------------------------------------
# Initial Population
# ----------------------------------------------------

INITIAL_ASTRONAUTS = 6

INITIAL_ROBOTS = 3

# ----------------------------------------------------
# Starting Resources
# ----------------------------------------------------

STARTING_POWER = 1000.0
STARTING_WATER = 600.0
STARTING_OXYGEN = 750.0
STARTING_FOOD = 400.0

# ----------------------------------------------------
# Buildings
# ----------------------------------------------------

INITIAL_HABITATS = 1
INITIAL_SOLAR_ARRAYS = 2

# ----------------------------------------------------
# Logging
# ----------------------------------------------------

LOG_LEVEL = "INFO"

# ----------------------------------------------------
# Random Seed
# ----------------------------------------------------

RANDOM_SEED = None
