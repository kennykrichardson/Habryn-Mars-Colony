"""Deterministic identity, personality, schedule, and visual variation."""
from __future__ import annotations

import random


PERSONALITY_TRAITS = (
    "introversion", "sociability", "discipline", "curiosity", "ambition",
    "empathy", "risk_tolerance", "stress_tolerance", "adaptability",
)

SUIT_COLORS = (
    (205, 190, 157), (185, 164, 137), (166, 187, 177), (189, 153, 131),
    (166, 174, 192), (210, 180, 126), (178, 181, 157),
)
VISOR_COLORS = ((74, 143, 164), (78, 120, 153), (74, 155, 143), (115, 130, 162))
ROBOT_TYPES = ("rover", "maintenance", "transport", "construction", "science")


def character_rng(seed: int | None, unique_id: int) -> random.Random:
    """Use an agent-local stream so creation order cannot change appearance."""
    seed_value = 0 if seed is None else int(seed)
    return random.Random((seed_value << 32) ^ int(unique_id) ^ 0x48414252594E)


def initialize_character(agent, seed: int | None) -> None:
    """Fill only absent state, keeping supplied scenario data authoritative."""
    rng = character_rng(seed, agent.unique_id)
    if not getattr(agent, "personality", None):
        agent.personality = {trait: round(rng.uniform(.25, .85), 2) for trait in PERSONALITY_TRAITS}
    if not getattr(agent, "appearance", None):
        profession = getattr(agent, "profession", "Astronaut")
        robot = "robot" in type(agent).__name__.lower()
        suit = SUIT_COLORS[rng.randrange(len(SUIT_COLORS))]
        visor = VISOR_COLORS[rng.randrange(len(VISOR_COLORS))]
        agent.appearance = {
            "robot_type": ROBOT_TYPES[(agent.unique_id - 1001) % len(ROBOT_TYPES)] if robot else None,
            "suit_color": suit,
            "trim_color": ((agent.unique_id * 37) % 120 + 90, (agent.unique_id * 59) % 100 + 95, (agent.unique_id * 23) % 120 + 85),
            "visor_color": visor,
            "helmet_style": rng.randrange(3),
            "backpack_style": rng.randrange(3),
            "ident_mark": f"{agent.unique_id % 100:02d}",
            "profession": profession,
            "accessory": profession.lower(),
        }
    else:
        agent.appearance = dict(agent.appearance)
        for color_name in ("suit_color", "trim_color", "visor_color"):
            if color_name in agent.appearance:
                agent.appearance[color_name] = tuple(agent.appearance[color_name])
    if not getattr(agent, "work_schedule", None):
        shift_start = 7 + rng.randrange(3)
        agent.work_schedule = {
            "wake_hour": 6 + rng.randrange(2),
            "work_start": shift_start,
            "work_end": min(20, shift_start + 8),
            "meal_hour": 12,
            "social_hour": 19,
            "sleep_hour": 22,
        }
    if not getattr(agent, "background", ""):
        profession = getattr(agent, "profession", "Colony Specialist")
        agent.background = f"{profession} recruited for the Mars settlement mission."


def default_personality() -> dict[str, float]:
    return {trait: .5 for trait in PERSONALITY_TRAITS}
