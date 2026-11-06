"""Small, cached pixel-art assets drawn entirely with Pygame primitives."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import random

import pygame

PALETTE = {
    "void": (24, 20, 24), "soil": (133, 69, 52), "soil_light": (164, 91, 64),
    "soil_dark": (91, 48, 43), "sand": (171, 109, 71), "rock": (99, 76, 68),
    "basalt": (65, 54, 55), "cream": (218, 189, 143), "cream_light": (242, 218, 174),
    "shadow": (55, 43, 43), "metal": (104, 123, 130), "cyan": (106, 205, 213),
    "blue": (66, 121, 149), "green": (119, 166, 116), "amber": (225, 160, 75),
    "red": (199, 81, 65), "glass": (62, 117, 130), "white": (247, 233, 197),
}

TERRAIN_COLORS = {
    "Plains": PALETTE["soil"], "Rock": PALETTE["rock"], "Sand": PALETTE["sand"],
    "Cliff": PALETTE["basalt"], "Ice": (118, 145, 148), "Crater": (102, 62, 55),
    "Lava Tube": (67, 52, 51),
}


def _seed(*parts: object) -> int:
    value = "|".join(map(str, parts)).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(value, digest_size=8).digest(), "little")


@lru_cache(maxsize=8192)
def terrain_tile(terrain: str, x: int, y: int, seed: int, explored: bool, platform: bool = False) -> pygame.Surface:
    """A deterministic 16×16 tile texture. Cache key includes world coordinates."""
    rng = random.Random(_seed(seed, terrain, x, y))
    surface = pygame.Surface((16, 16))
    base = PALETTE["shadow"] if platform else TERRAIN_COLORS.get(terrain, PALETTE["soil"])
    light = PALETTE["metal"] if platform else PALETTE["soil_light"]
    dark = PALETTE["shadow"] if platform else PALETTE["soil_dark"]
    surface.fill(base)
    if platform:
        for py in (3, 11):
            pygame.draw.line(surface, (76, 71, 68), (0, py), (15, py))
        pygame.draw.rect(surface, (125, 109, 93), (0, 0, 16, 1))
        pygame.draw.rect(surface, (38, 35, 37), (0, 15, 16, 1))
        for px, py in ((2, 2), (13, 2), (2, 13), (13, 13)):
            surface.set_at((px, py), PALETTE["amber"])
    else:
        for _ in range(19):
            px, py = rng.randrange(1, 15), rng.randrange(1, 15)
            color = light if rng.random() > .43 else dark
            surface.set_at((px, py), color)
            if rng.random() > .76:
                surface.set_at((min(15, px + 1), py), color)
        if terrain == "Crater":
            pygame.draw.rect(surface, dark, (3, 4, 9, 6))
            pygame.draw.rect(surface, light, (4, 3, 7, 1))
            pygame.draw.rect(surface, PALETTE["soil"], (5, 5, 5, 3))
        elif terrain in {"Rock", "Cliff", "Lava Tube"}:
            pygame.draw.rect(surface, dark, (4, 6, 8, 6))
            pygame.draw.rect(surface, light, (5, 5, 5, 2))
        elif terrain == "Sand":
            pygame.draw.line(surface, dark, (1, 12), (7, 10))
            pygame.draw.line(surface, light, (8, 4), (14, 3))
        elif terrain == "Ice":
            pygame.draw.line(surface, (190, 211, 200), (2, 4), (6, 8))
            pygame.draw.line(surface, (190, 211, 200), (11, 9), (14, 12))
    if not explored:
        shade = pygame.Surface((16, 16), pygame.SRCALPHA)
        shade.fill((17, 17, 23, 155))
        surface.blit(shade, (0, 0))
        # Visible, faint survey grid distinguishes unknown terrain.
        for p in (0, 8):
            pygame.draw.line(surface, (57, 50, 55), (p, 0), (p, 15))
            pygame.draw.line(surface, (57, 50, 55), (0, p), (15, p))
    return surface


def _building_art(surface: pygame.Surface, kind: str, online: bool, damaged: bool) -> None:
    w, h = surface.get_size()
    surface.fill((0, 0, 0, 0))
    if w < 8 or h < 8:
        return
    # Raised foundation and dark outline keep each sprite legible on every tile.
    pygame.draw.rect(surface, PALETTE["shadow"], (0, h - 4, w, 4))
    pygame.draw.rect(surface, (120, 91, 70), (1, h - 5, w - 2, 2))
    cx = w // 2
    if "Solar" in kind:
        pygame.draw.rect(surface, PALETTE["cream"], (2, h // 2, max(4, w // 3), max(4, h // 3)))
        for px in range(w // 2, w - 2, max(4, w // 6)):
            pygame.draw.rect(surface, PALETTE["blue"], (px, 3, max(3, w // 7), max(4, h - 8)))
            pygame.draw.line(surface, PALETTE["cyan"], (px + 1, 4), (px + 1, h - 6))
        pygame.draw.line(surface, PALETTE["metal"], (w // 2, h // 2), (w // 2, h - 5), 2)
    elif "Reactor" in kind:
        pygame.draw.rect(surface, PALETTE["cream"], (2, 4, w - 4, h - 8))
        pygame.draw.rect(surface, PALETTE["metal"], (4, 2, w - 8, 5))
        pygame.draw.rect(surface, PALETTE["amber"] if online else PALETTE["shadow"], (cx - 2, 7, 4, 4))
        pygame.draw.rect(surface, PALETTE["shadow"], (w - 8, 2, 3, h // 2))
    elif "Greenhouse" in kind:
        pygame.draw.rect(surface, PALETTE["metal"], (2, 4, w - 4, h - 9))
        pygame.draw.rect(surface, PALETTE["glass"], (4, 6, w - 8, h - 13))
        for px in range(6, w - 5, 5):
            pygame.draw.line(surface, PALETTE["cream"], (px, 6), (px, h - 5))
        pygame.draw.rect(surface, PALETTE["green"], (5, h // 2, 3, 3))
        pygame.draw.rect(surface, PALETTE["green"], (w - 9, h // 2 + 2, 3, 3))
    elif "Oxygen" in kind:
        pygame.draw.rect(surface, PALETTE["cream"], (3, 6, w - 6, h - 11))
        pygame.draw.rect(surface, PALETTE["cyan"], (5, 8, max(4, w - 10), max(4, h // 4)))
        for px in range(5, w - 4, 5):
            pygame.draw.rect(surface, PALETTE["metal"], (px, h // 2 + 2, 2, h // 4))
    elif "Water" in kind:
        pygame.draw.rect(surface, PALETTE["cream"], (3, 6, w - 6, h - 11))
        pygame.draw.rect(surface, PALETTE["blue"], (5, 8, w - 10, h // 3))
        pygame.draw.rect(surface, PALETTE["cyan"], (w - 7, 2, 3, h - 8))
    elif "Battery" in kind:
        pygame.draw.rect(surface, PALETTE["metal"], (3, 4, w - 6, h - 9))
        pygame.draw.rect(surface, PALETTE["cream"], (5, 2, w - 10, 3))
        pygame.draw.rect(surface, PALETTE["amber"] if online else PALETTE["shadow"], (w // 2 - 2, h // 2 - 2, 4, 5))
    elif "Medical" in kind:
        pygame.draw.rect(surface, PALETTE["cream"], (2, 5, w - 4, h - 10))
        pygame.draw.rect(surface, PALETTE["glass"], (4, 7, max(4, w - 8), max(4, h // 4)))
        pygame.draw.rect(surface, PALETTE["red"], (cx - 2, h // 2, 5, 3))
        pygame.draw.rect(surface, PALETTE["red"], (cx - 1, h // 2 - 1, 3, 5))
    elif "Storage" in kind:
        pygame.draw.rect(surface, PALETTE["cream"], (2, 5, w - 4, h - 10))
        pygame.draw.rect(surface, PALETTE["metal"], (2, 5, w - 4, 3))
        for px in range(5, w - 3, 7):
            pygame.draw.rect(surface, PALETTE["sand"], (px, h // 2, 5, max(3, h // 4)))
            pygame.draw.line(surface, PALETTE["shadow"], (px, h // 2), (px, h // 2 + max(3, h // 4)))
    elif "Workshop" in kind:
        pygame.draw.rect(surface, PALETTE["metal"], (2, 6, w - 4, h - 11))
        pygame.draw.rect(surface, PALETTE["cream"], (4, 8, w - 8, h - 15))
        pygame.draw.rect(surface, PALETTE["amber"], (5, h // 2 + 1, max(4, w // 4), 3))
        pygame.draw.line(surface, PALETTE["metal"], (w // 2, 3), (w // 2, h - 5), 2)
        pygame.draw.rect(surface, PALETTE["cyan"], (w - 8, 3, 4, 3))
    elif "Mine" in kind:
        pygame.draw.rect(surface, PALETTE["rock"], (1, h // 3, w - 2, h // 2))
        pygame.draw.rect(surface, PALETTE["shadow"], (w // 3, h // 2, w // 3, h // 3))
        pygame.draw.rect(surface, PALETTE["metal"], (cx - 1, 2, 2, h // 2))
        pygame.draw.rect(surface, PALETTE["amber"], (cx - 3, 2, 6, 2))
    elif "Recycling" in kind:
        pygame.draw.rect(surface, PALETTE["metal"], (3, h // 3, w - 6, h // 2))
        pygame.draw.rect(surface, PALETTE["green"], (5, h // 3 + 2, max(4, w // 4), max(4, h // 4)))
        pygame.draw.rect(surface, PALETTE["cyan"], (w - 9, 4, 4, h // 3))
        pygame.draw.rect(surface, PALETTE["cream"], (w - 11, 3, 8, 2))
    elif "Launch" in kind:
        pygame.draw.rect(surface, PALETTE["metal"], (1, h // 2, w - 2, h // 3))
        pygame.draw.rect(surface, PALETTE["shadow"], (3, h // 2 + 2, w - 6, 3))
        pygame.draw.rect(surface, PALETTE["cream"], (cx - 2, 2, 4, h // 2))
        pygame.draw.polygon(surface, PALETTE["red"], [(cx - 3, h // 3), (cx, h // 4), (cx + 3, h // 3)])
        pygame.draw.rect(surface, PALETTE["amber"], (cx - 2, h // 2 - 2, 4, 3))
    elif "Laboratory" in kind:
        pygame.draw.rect(surface, PALETTE["cream"], (2, h // 2, w - 4, h // 3))
        pygame.draw.rect(surface, PALETTE["glass"], (4, 4, w - 8, h // 2))
        pygame.draw.rect(surface, PALETTE["cyan"], (6, h // 3, w - 12, 4))
        pygame.draw.rect(surface, PALETTE["metal"], (cx - 2, 2, 4, 3))
    elif "Communications" in kind:
        pygame.draw.rect(surface, PALETTE["cream"], (3, h // 2, w - 6, h // 3))
        pygame.draw.line(surface, PALETTE["metal"], (cx, h // 2), (cx, 3), 2)
        pygame.draw.arc(surface, PALETTE["cyan"], (cx - 7, 1, 14, 12), 0, 3.14, 2)
        pygame.draw.circle(surface, PALETTE["amber"], (cx, 5), 2)
    elif "Habitat" in kind:
        body_y = max(4, h // 3)
        pygame.draw.rect(surface, PALETTE["cream"], (2, body_y, w - 4, h - body_y - 5))
        pygame.draw.rect(surface, (174, 143, 109), (3, body_y, w - 6, 2))
        pygame.draw.rect(surface, PALETTE["glass"], (5, body_y + 4, 5, 4))
        pygame.draw.rect(surface, PALETTE["shadow"], (cx - 3, h - 12, 6, 7))
        pygame.draw.rect(surface, PALETTE["metal"], (0, body_y + 2, 3, h // 3))
    else:  # Habitats and all other existing facilities use a modular module silhouette.
        body_y = max(4, h // 3)
        pygame.draw.rect(surface, PALETTE["cream"], (2, body_y, w - 4, h - body_y - 5))
        pygame.draw.rect(surface, (174, 143, 109), (3, body_y, w - 6, 2))
        window_count = max(1, (w - 12) // 7)
        for i in range(window_count):
            px = 5 + i * max(6, (w - 10) // window_count)
            pygame.draw.rect(surface, PALETTE["glass"], (px, body_y + 4, 4, 4))
        pygame.draw.rect(surface, PALETTE["shadow"], (cx - 3, h - 12, 6, 7))
        pygame.draw.rect(surface, PALETTE["amber"] if online else PALETTE["shadow"], (cx - 1, h - 10, 2, 2))
        pygame.draw.rect(surface, PALETTE["metal"], (0, body_y + 2, 3, h // 3))
    # Actual operational fields drive small lamps and damage marks.
    pygame.draw.rect(surface, (126, 195, 126) if online else PALETTE["red"], (w - 5, 1, 3, 3))
    if damaged:
        pygame.draw.line(surface, PALETTE["red"], (2, 2), (min(w - 2, 8), min(h - 2, 8)), 2)


@lru_cache(maxsize=512)
def building_sprite(kind: str, width: int, height: int, online: bool, damaged: bool) -> pygame.Surface:
    width, height = max(8, width), max(8, height)
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    _building_art(surface, kind, online, damaged)
    return surface


def _freeze(value):
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(item) for item in value)
    return value


def character_sprite(
    robot: bool,
    frame: int,
    direction: int,
    working: bool,
    appearance: dict | None = None,
    activity: str | None = None,
) -> pygame.Surface:
    """Return an identity-specific detailed sprite frame at native pixel scale."""
    appearance = appearance or {}
    appearance_key = tuple(sorted((key, _freeze(value)) for key, value in appearance.items()))
    action = (activity or ("working" if working else "idle")).lower()
    return _character_sprite_cached(robot, frame % 4, direction % 4, appearance_key, action)


@lru_cache(maxsize=2048)
def _character_sprite_cached(robot: bool, frame: int, direction: int, appearance_key: tuple,
                             activity: str) -> pygame.Surface:
    appearance = dict(appearance_key)
    sprite = pygame.Surface((64, 56) if robot else (48, 64), pygame.SRCALPHA)
    if robot:
        _draw_robot(sprite, frame, direction, activity, appearance)
    else:
        _draw_astronaut(sprite, frame, direction, activity, appearance)
    return sprite


def _draw_astronaut(sprite: pygame.Surface, frame: int, direction: int, action: str, appearance: dict) -> None:
    suit = tuple(appearance.get("suit_color", PALETTE["cream_light"]))
    trim = tuple(appearance.get("trim_color", PALETTE["red"]))
    visor = tuple(appearance.get("visor_color", PALETTE["glass"]))
    dark = tuple(max(0, channel - 65) for channel in suit)
    light = tuple(min(255, channel + 30) for channel in suit)
    mark = str(appearance.get("ident_mark", "07"))
    helmet_style = int(appearance.get("helmet_style", 0))
    pack_style = int(appearance.get("backpack_style", 0))
    accessory = str(appearance.get("accessory", appearance.get("profession", ""))).lower()
    outline = PALETTE["shadow"]
    stride = frame % 2 if action in {"walking", "walk", "turning"} else 0
    pygame.draw.ellipse(sprite, (46, 35, 34), (8, 59, 33, 4))

    # Life-support pack, frame, hoses and clipped equipment.
    pygame.draw.rect(sprite, outline, (5, 22, 12, 30))
    pygame.draw.rect(sprite, (80, 98, 101), (7, 24, 9, 25))
    pygame.draw.rect(sprite, (128, 143, 137), (8, 25, 7, 2))
    pygame.draw.rect(sprite, PALETTE["cyan"], (9, 29, 3, 12))
    pygame.draw.rect(sprite, PALETTE["amber"], (13, 29, 2, 5))
    if pack_style == 1:
        pygame.draw.rect(sprite, PALETTE["blue"], (3, 32, 4, 10))
        pygame.draw.rect(sprite, PALETTE["cream"], (3, 31, 5, 2))
    elif pack_style == 2:
        pygame.draw.rect(sprite, PALETTE["metal"], (6, 45, 10, 5))
        pygame.draw.rect(sprite, PALETTE["amber"], (7, 46, 2, 2))
        pygame.draw.rect(sprite, PALETTE["red"], (12, 46, 2, 2))
    pygame.draw.rect(sprite, trim, (8, 43, 7, 2))
    pygame.draw.line(sprite, (188, 154, 117), (16, 29), (19, 34), 2)

    # Legs, reinforced knees and magnetic boots.
    left_leg_x = 16 + stride * 2
    right_leg_x = 27 - stride * 2
    for leg_x in (left_leg_x, right_leg_x):
        pygame.draw.rect(sprite, outline, (leg_x - 1, 43, 9, 15))
        pygame.draw.rect(sprite, suit, (leg_x, 44, 7, 10))
        pygame.draw.rect(sprite, trim, (leg_x, 50, 7, 2))
        pygame.draw.rect(sprite, (85, 87, 84), (leg_x - 1, 55, 9, 5))
        pygame.draw.rect(sprite, PALETTE["metal"], (leg_x, 56, 7, 1))
        pygame.draw.rect(sprite, light, (leg_x + 2, 45, 3, 3))

    # Torso with layered pressure suit, collar ring, seams and control module.
    pygame.draw.rect(sprite, outline, (14, 23, 22, 25))
    pygame.draw.rect(sprite, dark, (15, 25, 20, 21))
    pygame.draw.rect(sprite, suit, (17, 25, 16, 20))
    pygame.draw.rect(sprite, light, (18, 26, 2, 17))
    pygame.draw.rect(sprite, trim, (17, 26, 16, 2))
    pygame.draw.rect(sprite, (100, 105, 101), (18, 22, 15, 4))
    pygame.draw.rect(sprite, (203, 197, 174), (19, 22, 13, 2))
    pygame.draw.rect(sprite, outline, (21, 30, 11, 11))
    pygame.draw.rect(sprite, (61, 75, 80), (22, 31, 9, 9))
    pygame.draw.rect(sprite, visor, (23, 32, 7, 3))
    pygame.draw.rect(sprite, trim, (23, 36, 3, 3))
    pygame.draw.rect(sprite, PALETTE["amber"], (28, 36, 2, 2))
    pygame.draw.rect(sprite, (177, 184, 169), (18, 41, 14, 2))
    # Tiny but readable mission markings, rendered as pixel bars.
    digits = [int(c) for c in mark[-2:] if c.isdigit()]
    for index, digit in enumerate(digits):
        for bit in range(3):
            if digit & (1 << bit):
                sprite.set_at((18 + index * 4 + bit % 2, 29 + bit), trim)

    # Arms, elbow joints, gloves, suit seams and action pose.
    arm_lift = 3 if action in {"working", "repairing", "operating equipment", "emergency response"} else 0
    swing = stride * 2 if action in {"walking", "walk"} else 0
    for side, arm_x in ((-1, 10), (1, 33)):
        pygame.draw.rect(sprite, outline, (arm_x, 27 + arm_lift, 7, 17))
        pygame.draw.rect(sprite, suit, (arm_x + 1, 28 + arm_lift, 5, 12))
        pygame.draw.rect(sprite, trim, (arm_x + 1, 34 + arm_lift, 5, 2))
        glove_y = 40 + arm_lift + (swing if side < 0 else -swing)
        pygame.draw.rect(sprite, outline, (arm_x, glove_y, 7, 6))
        pygame.draw.rect(sprite, light, (arm_x + 1, glove_y + 1, 5, 3))
        pygame.draw.rect(sprite, (173, 156, 128), (arm_x + 1, glove_y + 4, 2, 1))

    # Helmet shape, rim, visor with two crisp reflection bands.
    helmet_x = 13 if helmet_style == 1 else 14
    helmet_w = 22 if helmet_style == 1 else 20
    pygame.draw.rect(sprite, outline, (helmet_x, 3, helmet_w, 21))
    pygame.draw.rect(sprite, suit, (helmet_x + 2, 4, helmet_w - 4, 17))
    pygame.draw.rect(sprite, light, (helmet_x + 3, 5, helmet_w - 6, 2))
    pygame.draw.rect(sprite, trim, (helmet_x + 1, 19, helmet_w - 2, 3))
    visor_y = 9 if direction == 0 else 10
    visor_x = helmet_x + (4 if direction == 3 else helmet_w - 9 if direction == 1 else 3)
    visor_w = 7 if direction in (1, 3) else helmet_w - 6
    visor_h = 6 if helmet_style != 2 else 5
    pygame.draw.rect(sprite, (31, 49, 58), (visor_x, visor_y, visor_w, visor_h))
    if direction != 0:
        pygame.draw.rect(sprite, visor, (visor_x + 1, visor_y + 1, visor_w - 2, visor_h - 2))
        pygame.draw.rect(sprite, (194, 222, 212), (visor_x + 2, visor_y + 1, max(2, visor_w // 3), 1))
        pygame.draw.rect(sprite, (122, 183, 193), (visor_x + visor_w - 3, visor_y + 3, 1, 2))
    else:
        pygame.draw.rect(sprite, outline, (visor_x, visor_y, visor_w, visor_h))
        pygame.draw.rect(sprite, trim, (helmet_x + 5, 11, 10, 2))
    if helmet_style == 1:
        pygame.draw.rect(sprite, PALETTE["amber"], (helmet_x - 2, 10, 2, 6))
    elif helmet_style == 2:
        pygame.draw.rect(sprite, PALETTE["metal"], (helmet_x + 2, 2, helmet_w - 4, 3))
        pygame.draw.rect(sprite, PALETTE["amber"], (helmet_x + helmet_w - 5, 6, 3, 2))

    # Profession-specific clipped kit and activity cues.
    if "engineer" in accessory or "robot" in accessory:
        pygame.draw.rect(sprite, (178, 164, 131), (36, 35, 3, 12))
        pygame.draw.rect(sprite, PALETTE["metal"], (34, 34, 7, 3))
        pygame.draw.rect(sprite, PALETTE["amber"], (34, 33, 2, 2))
    elif "scient" in accessory or "research" in accessory:
        pygame.draw.rect(sprite, PALETTE["cyan"], (37, 35, 5, 8))
        pygame.draw.rect(sprite, PALETTE["green"], (38, 37, 3, 3))
        pygame.draw.rect(sprite, PALETTE["cream"], (38, 34, 3, 1))
    elif "farm" in accessory or "botan" in accessory:
        pygame.draw.rect(sprite, PALETTE["green"], (37, 37, 5, 4))
        pygame.draw.line(sprite, (181, 208, 133), (39, 37), (42, 34))
    elif "medic" in accessory:
        pygame.draw.rect(sprite, PALETTE["white"], (36, 35, 7, 7))
        pygame.draw.rect(sprite, PALETTE["red"], (39, 36, 2, 5))
        pygame.draw.rect(sprite, PALETTE["red"], (37, 38, 6, 2))
    else:
        pygame.draw.rect(sprite, PALETTE["blue"], (36, 35, 5, 8))
        pygame.draw.rect(sprite, PALETTE["amber"], (37, 36, 3, 2))

    if action == "eating":
        pygame.draw.rect(sprite, PALETTE["amber"], (34, 25, 3, 4))
    elif action == "sleeping":
        pygame.draw.rect(sprite, PALETTE["shadow"], (helmet_x + 4, visor_y + 2, visor_w - 8, 1))
    elif action == "socializing":
        pygame.draw.rect(sprite, PALETTE["cream"], (39, 13, 7, 5))
        pygame.draw.rect(sprite, PALETTE["cyan"], (41, 14, 1, 1))
        pygame.draw.rect(sprite, PALETTE["cyan"], (44, 14, 1, 1))
    elif action in {"repairing", "operating equipment", "emergency response"}:
        pygame.draw.rect(sprite, PALETTE["amber"], (41, 40 - frame % 2, 2, 2))


def _draw_robot(sprite: pygame.Surface, frame: int, direction: int, action: str, appearance: dict) -> None:
    kind = str(appearance.get("robot_type", "rover"))
    trim = tuple(appearance.get("trim_color", PALETTE["cyan"]))
    body = tuple(appearance.get("suit_color", PALETTE["metal"]))
    outline = PALETTE["shadow"]
    if kind in {"rover", "transport"}:
        wheel_y = 43
        wheel_count = 6 if kind == "rover" else 4
        for index in range(wheel_count):
            x = 5 + index * (52 // max(1, wheel_count - 1))
            offset = frame % 2 if action in {"walking", "walk", "turning"} else 0
            pygame.draw.rect(sprite, outline, (x, wheel_y, 8, 10))
            pygame.draw.rect(sprite, PALETTE["metal"], (x + 2, wheel_y + 2, 4, 6))
            pygame.draw.rect(sprite, PALETTE["amber"], (x + 3, wheel_y + 3 + offset, 2, 2))
        pygame.draw.rect(sprite, outline, (7, 24, 50, 22))
        pygame.draw.rect(sprite, body, (9, 25, 46, 18))
        pygame.draw.rect(sprite, trim, (11, 27, 42, 3))
        if kind == "transport":
            for x in (15, 25, 35, 45):
                pygame.draw.rect(sprite, (177, 143, 102), (x, 15, 8, 10))
                pygame.draw.line(sprite, PALETTE["cream"], (x + 1, 17), (x + 6, 17))
        else:
            pygame.draw.rect(sprite, PALETTE["cyan"], (19, 31, 18, 7))
            pygame.draw.rect(sprite, (199, 222, 204), (21, 32, 5, 2))
    elif kind == "construction":
        pygame.draw.rect(sprite, outline, (12, 28, 39, 22))
        pygame.draw.rect(sprite, body, (14, 30, 35, 17))
        pygame.draw.rect(sprite, trim, (18, 32, 12, 7))
        pygame.draw.rect(sprite, PALETTE["amber"], (20, 34, 7, 3))
        for x in (14, 43):
            pygame.draw.rect(sprite, outline, (x, 47, 11, 6))
            pygame.draw.rect(sprite, PALETTE["metal"], (x + 2, 48, 7, 4))
        arm_raise = frame % 3 if action in {"working", "repairing", "operating equipment"} else 0
        pygame.draw.rect(sprite, PALETTE["metal"], (46, 22 - arm_raise, 4, 13))
        pygame.draw.rect(sprite, PALETTE["amber"], (44, 19 - arm_raise, 8, 5))
    elif kind == "maintenance":
        pygame.draw.rect(sprite, outline, (21, 11, 25, 39))
        pygame.draw.rect(sprite, body, (23, 13, 21, 34))
        pygame.draw.rect(sprite, PALETTE["cyan"], (26, 15, 15, 8))
        pygame.draw.rect(sprite, PALETTE["amber"], (30, 17, 5, 3))
        for y in (30, 41):
            pygame.draw.rect(sprite, outline, (17, y, 31, 4))
            pygame.draw.rect(sprite, PALETTE["metal"], (19, y, 27, 2))
        pygame.draw.rect(sprite, PALETTE["metal"], (12, 29, 10, 4))
        pygame.draw.rect(sprite, PALETTE["metal"], (45, 40, 8, 4))
        pygame.draw.rect(sprite, PALETTE["amber"], (7, 27, 6, 8))
        pygame.draw.rect(sprite, PALETTE["amber"], (52, 38, 6, 8))
    else:  # science rover: mast camera, instrument bay and sample arm.
        pygame.draw.rect(sprite, outline, (8, 25, 48, 23))
        pygame.draw.rect(sprite, body, (10, 27, 44, 18))
        pygame.draw.rect(sprite, trim, (12, 29, 40, 3))
        for x in (12, 25, 38, 49):
            pygame.draw.rect(sprite, PALETTE["metal"], (x, 44, 7, 9))
            pygame.draw.rect(sprite, outline, (x - 1, 50, 9, 5))
        pygame.draw.rect(sprite, PALETTE["metal"], (30, 5, 4, 22))
        pygame.draw.rect(sprite, PALETTE["red"], (24, 4, 17, 8))
        pygame.draw.rect(sprite, PALETTE["cyan"], (27, 6, 5, 4))
        pygame.draw.rect(sprite, PALETTE["amber"], (35, 6, 3, 3))
        pygame.draw.rect(sprite, PALETTE["metal"], (52, 30, 5, 15))
        pygame.draw.rect(sprite, PALETTE["amber"], (53, 43, 7, 4))
    if direction == 0:
        pygame.draw.rect(sprite, PALETTE["cream"], (28, 28, 8, 2))
    elif direction in (1, 3):
        pygame.draw.rect(sprite, PALETTE["cyan"], (8 if direction == 3 else 51, 32, 5, 4))
    if action in {"repairing", "working", "operating equipment", "emergency response"} and frame % 2:
        pygame.draw.rect(sprite, PALETTE["amber"], (54, 17, 3, 3))


def deposit_marker(kind: str, size: int = 8) -> pygame.Surface:
    color = PALETTE["cyan"] if "Water" in kind or "Ice" in kind else PALETTE["amber"]
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    points = [(size // 2, 0), (size - 1, size // 2), (size // 2, size - 1), (0, size // 2)]
    pygame.draw.polygon(image, PALETTE["shadow"], points)
    inner = [(size // 2, 2), (size - 2, size // 2), (size // 2, size - 2), (2, size // 2)]
    pygame.draw.polygon(image, color, inner)
    return image
