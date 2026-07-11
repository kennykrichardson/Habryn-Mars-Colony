"""
meteor_system.py

Part 1/4

Canonical meteor impact system.

Responsible for

- meteor spawning
- trajectories
- impact prediction
- impact locations
- damage estimation
- resource deposits

Does NOT repair damage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random

# ============================================================
# Meteor Types
# ============================================================


class MeteorType(Enum):

    STONE = "Stone"

    IRON = "Iron"

    ICE = "Ice"

    NICKEL = "Nickel"

    RARE = "Rare"


# ============================================================
# Meteor
# ============================================================


@dataclass(slots=True)
class Meteor:

    meteor_type: MeteorType

    position: tuple[float, float]

    velocity: tuple[float, float]

    size: float

    mass: float

    damage_radius: float

    impact_damage: float

    active: bool = True

    impacted: bool = False


# ============================================================
# Meteor System
# ============================================================


@dataclass
class MeteorSystem:

    width: int = 100

    height: int = 100

    meteors: list[Meteor] = field(default_factory=list)

    impacts: int = 0

    destroyed_buildings: int = 0

    generated_resources: dict[
        str,
        float,
    ] = field(default_factory=dict)

    # ========================================================
    # Spawning
    # ========================================================

    def spawn(
        self,
    ) -> Meteor:

        meteor_type = random.choice(list(MeteorType))

        meteor = Meteor(
            meteor_type=meteor_type,
            position=(
                random.uniform(
                    0,
                    self.width,
                ),
                -10.0,
            ),
            velocity=(
                random.uniform(
                    -0.5,
                    0.5,
                ),
                random.uniform(
                    1.0,
                    3.0,
                ),
            ),
            size=random.uniform(
                0.5,
                5.0,
            ),
            mass=random.uniform(
                50,
                5000,
            ),
            damage_radius=random.uniform(
                2,
                12,
            ),
            impact_damage=random.uniform(
                20,
                100,
            ),
        )

        self.meteors.append(
            meteor,
        )

        return meteor

    # ========================================================
    # Runtime
    # ========================================================

    def step(
        self,
    ) -> None:

        remaining: list[Meteor] = []

        for meteor in self.meteors:

            if not meteor.active:

                continue

            x, y = meteor.position

            vx, vy = meteor.velocity

            meteor.position = (
                x + vx,
                y + vy,
            )

            if meteor.position[1] >= self.height:

                self.impact(
                    meteor,
                )

            else:

                remaining.append(
                    meteor,
                )

        self.meteors = remaining

    # ========================================================
    # Impact
    # ========================================================

    def impact(
        self,
        meteor: Meteor,
    ) -> None:

        meteor.active = False

        meteor.impacted = True

        self.impacts += 1

        self._generate_resources(
            meteor,
        )

    def _generate_resources(
        self,
        meteor: Meteor,
    ) -> None:

        resource = meteor.meteor_type.value.lower()

        self.generated_resources[resource] = (
            self.generated_resources.get(
                resource,
                0.0,
            )
            + meteor.mass
        )

    # ========================================================
    # Queries
    # ========================================================

    def active_meteors(
        self,
    ) -> list[Meteor]:

        return [meteor for meteor in self.meteors if meteor.active]

    def impacted_meteors(
        self,
    ) -> int:

        return self.impacts

    def total_resources(
        self,
    ) -> float:

        return sum(self.generated_resources.values())

        # ========================================================

    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        return {
            "active_meteors": len(
                self.active_meteors(),
            ),
            "total_impacts": self.impacts,
            "destroyed_buildings": self.destroyed_buildings,
            "generated_resources": dict(
                self.generated_resources,
            ),
            "resource_mass": round(
                self.total_resources(),
                2,
            ),
        }

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        return {
            "impacts": self.impacts,
            "destroyed_buildings": self.destroyed_buildings,
            "generated_resources": dict(
                self.generated_resources,
            ),
            "meteors": [
                {
                    "meteor_type": meteor.meteor_type.value,
                    "position": meteor.position,
                    "velocity": meteor.velocity,
                    "size": meteor.size,
                    "mass": meteor.mass,
                    "damage_radius": meteor.damage_radius,
                    "impact_damage": meteor.impact_damage,
                    "active": meteor.active,
                    "impacted": meteor.impacted,
                }
                for meteor in self.meteors
            ],
        }

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "MeteorSystem":

        system = cls()

        system.impacts = data.get(
            "impacts",
            0,
        )

        system.destroyed_buildings = data.get(
            "destroyed_buildings",
            0,
        )

        system.generated_resources = dict(
            data.get(
                "generated_resources",
                {},
            )
        )

        for meteor_data in data.get(
            "meteors",
            [],
        ):

            system.meteors.append(
                Meteor(
                    meteor_type=MeteorType(meteor_data["meteor_type"]),
                    position=tuple(meteor_data["position"]),
                    velocity=tuple(meteor_data["velocity"]),
                    size=meteor_data["size"],
                    mass=meteor_data["mass"],
                    damage_radius=meteor_data["damage_radius"],
                    impact_damage=meteor_data["impact_damage"],
                    active=meteor_data.get(
                        "active",
                        True,
                    ),
                    impacted=meteor_data.get(
                        "impacted",
                        False,
                    ),
                )
            )

        return system

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "MeteorSystem("
            f"active={len(self.active_meteors())}, "
            f"impacts={self.impacts}, "
            f"resources={len(self.generated_resources)}"
            ")"
        )


# ============================================================
# Canonical Alias
# ============================================================

MeteorManager = MeteorSystem
