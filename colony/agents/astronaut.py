"""
astronaut.py

Part 1/4

Canonical Astronaut implementation.

Inheritance

BaseAgent
    └── Astronaut

Every human colonist inherits from Astronaut.
Engineer, Scientist, Medic, Farmer, etc.
extend this class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .base_agent import BaseAgent, AgentState, InventoryItem

# ============================================================
# EVA Status
# ============================================================


class EVAStatus(Enum):

    INSIDE = "Inside"

    PREPARING = "Preparing"

    EVA = "EVA"

    RETURNING = "Returning"


# ============================================================
# Astronaut
# ============================================================


@dataclass
class Astronaut(BaseAgent):

    age: int = 30

    experience: int = 0

    level: int = 1

    eva_status: EVAStatus = EVAStatus.INSIDE

    suit_integrity: float = 100.0

    suit_oxygen: float = 100.0

    radiation: float = 0.0

    skill_levels: dict[str, int] = field(default_factory=dict)

    relationships: dict[int, float] = field(default_factory=dict)

    memories: list[str] = field(default_factory=list)

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        super().__post_init__()

        if not self.profession:

            self.profession = "Astronaut"

        self.skill_levels.setdefault(
            "general",
            1,
        )

    # ========================================================
    # EVA
    # ========================================================

    def prepare_eva(
        self,
    ) -> None:

        self.eva_status = EVAStatus.PREPARING

    def begin_eva(
        self,
    ) -> None:

        self.outside = True

        self.eva_status = EVAStatus.EVA

        self.state = AgentState.EVA

    def end_eva(
        self,
    ) -> None:

        self.outside = False

        self.eva_status = EVAStatus.INSIDE

        self.state = AgentState.IDLE

    def eva_update(
        self,
    ) -> None:

        if not self.outside:

            return

        self.suit_oxygen = max(
            0.0,
            self.suit_oxygen - 1.0,
        )

        self.suit_integrity = max(
            0.0,
            self.suit_integrity - 0.02,
        )

        self.radiation += 0.01

        if self.suit_oxygen <= 0:

            self.take_damage(
                2.0,
            )

        # ========================================================

    # Skills
    # ========================================================

    def add_experience(
        self,
        amount: int = 1,
    ) -> None:

        self.experience += max(
            0,
            amount,
        )

        while self.experience >= (self.level * 100):

            self.experience -= self.level * 100

            self.level += 1

    def improve_skill(
        self,
        skill: str,
        amount: int = 1,
    ) -> None:

        self.skill_levels[skill] = (
            self.skill_levels.get(
                skill,
                0,
            )
            + amount
        )

    def skill_level(
        self,
        skill: str,
    ) -> int:

        return self.skill_levels.get(
            skill,
            0,
        )

    # ========================================================
    # Relationships
    # ========================================================

    def change_relationship(
        self,
        astronaut_id: int,
        amount: float,
    ) -> None:

        value = self.relationships.get(
            astronaut_id,
            0.0,
        )

        value += amount

        value = max(
            -100.0,
            min(
                100.0,
                value,
            ),
        )

        self.relationships[astronaut_id] = value

    def relationship_with(
        self,
        astronaut_id: int,
    ) -> float:

        return self.relationships.get(
            astronaut_id,
            0.0,
        )

    # ========================================================
    # Memory
    # ========================================================

    def remember(
        self,
        memory: str,
    ) -> None:

        self.memories.append(
            memory,
        )

    def forget(
        self,
        index: int,
    ) -> None:

        if 0 <= index < len(self.memories):

            self.memories.pop(
                index,
            )

    def clear_memories(
        self,
    ) -> None:

        self.memories.clear()

    # ========================================================
    # Updates
    # ========================================================

    def hourly_update(
        self,
        needs_intensity: float = 1.0,
    ) -> None:

        super().hourly_update(needs_intensity)

        if self.outside:

            self.eva_update()

        if self.radiation > 50:

            self.change_stress(
                0.5,
            )

        if self.health < 50:

            self.change_morale(
                -0.25,
            )

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

        self.radiation = max(
            0.0,
            self.radiation - 0.1,
        )

        # ========================================================

    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data["eva_status"] = self.eva_status.value

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Astronaut":

        data = dict(data)
        inventory_data = data.pop("inventory", {})
        if isinstance(data.get("state"), str):
            data["state"] = AgentState(data["state"])
        if isinstance(data.get("position"), list):
            data["position"] = tuple(data["position"])
        if isinstance(data.get("destination"), list):
            data["destination"] = tuple(data["destination"])
        if isinstance(data.get("path"), list):
            data["path"] = [tuple(position) for position in data["path"]]
        if isinstance(data.get("relationships"), dict):
            data["relationships"] = {int(key): value for key, value in data["relationships"].items()}

        eva_status = EVAStatus(
            data.pop(
                "eva_status",
            ),
        )

        astronaut = cls(
            **data,
        )

        astronaut.inventory = {name: InventoryItem(name=name, quantity=values["quantity"],
                                                   weight=values["weight"])
                               for name, values in inventory_data.items()}

        astronaut.eva_status = eva_status

        return astronaut

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "age": self.age,
                "level": self.level,
                "experience": self.experience,
                "eva_status": self.eva_status.value,
                "suit_integrity": round(
                    self.suit_integrity,
                    2,
                ),
                "suit_oxygen": round(
                    self.suit_oxygen,
                    2,
                ),
                "radiation": round(
                    self.radiation,
                    2,
                ),
                "skills": dict(
                    self.skill_levels,
                ),
                "relationships": len(
                    self.relationships,
                ),
                "memories": len(
                    self.memories,
                ),
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "Astronaut("
            f"id={self.unique_id}, "
            f"name='{self.name}', "
            f"profession='{self.profession}', "
            f"level={self.level}, "
            f"state='{self.state.value}'"
            ")"
        )

    # ============================================================
    # Canonical Alias
    # ============================================================


Human = Astronaut
