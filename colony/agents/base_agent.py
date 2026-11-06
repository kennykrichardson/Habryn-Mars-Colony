"""
base_agent.py

Part 1/4

Canonical base class for every autonomous entity in Habryn.

Inheritance

BaseAgent
├── Astronaut
│   ├── Engineer
│   ├── Scientist
│   ├── Medic
│   ├── Farmer
│   ├── Miner
│   ├── Pilot
│   └── Security
│
└── Robot
    ├── BuilderBot
    ├── MiningBot
    ├── RepairBot
    └── CargoBot

This class intentionally knows nothing about Mars, buildings,
economy, AI, or the colony. It only represents an autonomous entity.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from math import dist
from typing import Any

# ============================================================
# Agent State
# ============================================================


class AgentState(Enum):

    IDLE = "Idle"

    WALKING = "Walking"

    WORKING = "Working"

    SLEEPING = "Sleeping"

    EATING = "Eating"

    DRINKING = "Drinking"

    REPAIRING = "Repairing"

    BUILDING = "Building"

    MINING = "Mining"

    RESEARCHING = "Researching"

    EVA = "EVA"

    INJURED = "Injured"

    SOCIALIZING = "Socializing"

    OPERATING = "Operating Equipment"

    EMERGENCY = "Emergency Response"

    DEAD = "Dead"


# ============================================================
# Inventory Item
# ============================================================


@dataclass(slots=True)
class InventoryItem:

    name: str

    quantity: float = 0.0

    weight: float = 0.0


# ============================================================
# Base Agent
# ============================================================


@dataclass
class BaseAgent:

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    unique_id: int

    name: str

    profession: str

    position: tuple[int, int]

    # --------------------------------------------------------
    # Movement
    # --------------------------------------------------------

    destination: tuple[int, int] | None = None

    speed: float = 1.0

    moving: bool = False

    outside: bool = False

    path: list[tuple[int, int]] = field(default_factory=list)

    # --------------------------------------------------------
    # Health
    # --------------------------------------------------------

    health: float = 100.0

    max_health: float = 100.0

    alive: bool = True

    # --------------------------------------------------------
    # Needs
    # --------------------------------------------------------

    oxygen: float = 100.0

    hunger: float = 0.0

    thirst: float = 0.0

    fatigue: float = 0.0

    stress: float = 0.0

    morale: float = 100.0

    # --------------------------------------------------------
    # Inventory
    # --------------------------------------------------------

    inventory: dict[str, InventoryItem] = field(default_factory=dict)

    max_inventory_weight: float = 50.0

    # --------------------------------------------------------
    # Tasks
    # --------------------------------------------------------

    current_task: Any | None = None

    task_queue: list[Any] = field(default_factory=list)

    priority: int = 5

    busy: bool = False

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    distance_travelled: float = 0.0

    tasks_completed: int = 0

    hours_worked: int = 0

    hours_alive: int = 0

    # --------------------------------------------------------
    # Runtime
    # --------------------------------------------------------

    state: AgentState = AgentState.IDLE

    personality: dict[str, float] = field(default_factory=dict)

    appearance: dict[str, Any] = field(default_factory=dict)

    background: str = ""

    employment_status: str = "Available"

    work_schedule: dict[str, int] = field(default_factory=dict)

    workplace_id: int | None = None

    current_activity: str = "Idle"

    next_activity: str = "Work"

    decision_reason: str = "Awaiting assignment"

    activity_until_tick: int = 0

    social_need: float = 0.0

    recreation_need: float = 0.0

    metadata: dict[str, Any] = field(default_factory=dict)

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(self) -> None:

        self.health = min(
            self.health,
            self.max_health,
        )

        self.oxygen = max(
            0.0,
            min(100.0, self.oxygen),
        )

        self.hunger = max(
            0.0,
            min(100.0, self.hunger),
        )

        self.thirst = max(
            0.0,
            min(100.0, self.thirst),
        )

        self.fatigue = max(
            0.0,
            min(100.0, self.fatigue),
        )

        self.stress = max(
            0.0,
            min(100.0, self.stress),
        )

        self.morale = max(
            0.0,
            min(100.0, self.morale),
        )

        if self.health <= 0:

            self.alive = False

            self.state = AgentState.DEAD

    # ========================================================
    # Properties
    # ========================================================

    @property
    def carrying_weight(
        self,
    ) -> float:

        total = 0.0

        for item in self.inventory.values():

            total += item.quantity * item.weight

        return total

    @property
    def inventory_full(
        self,
    ) -> bool:

        return self.carrying_weight >= self.max_inventory_weight

    @property
    def idle(
        self,
    ) -> bool:

        return self.state == AgentState.IDLE

    @property
    def dead(
        self,
    ) -> bool:

        return not self.alive

    @property
    def can_work(
        self,
    ) -> bool:

        return (
            self.alive
            and self.health > 0
            and self.oxygen > 0
            and self.state != AgentState.DEAD
        )

    # ========================================================
    # Movement
    # ========================================================

    def move_to(
        self,
        destination: tuple[int, int],
    ) -> None:

        if not self.can_work:

            return

        self.destination = destination

        self.moving = True

        self.state = AgentState.WALKING

    def stop(
        self,
    ) -> None:

        self.destination = None

        self.path.clear()

        self.moving = False

        if self.alive:

            self.state = AgentState.IDLE
            self.current_activity = "Idle"

    def follow_path(
        self,
    ) -> None:

        if not self.path:

            self.stop()

            return

        previous = self.position

        self.position = self.path.pop(0)

        self.distance_travelled += dist(
            previous,
            self.position,
        )

        if not self.path:

            self.stop()

        # ========================================================

    # Inventory
    # ========================================================

    def add_item(
        self,
        name: str,
        quantity: float = 1.0,
        weight: float = 0.0,
    ) -> bool:

        additional_weight = quantity * weight

        if self.carrying_weight + additional_weight > self.max_inventory_weight:
            return False

        if name not in self.inventory:

            self.inventory[name] = InventoryItem(
                name=name,
                quantity=quantity,
                weight=weight,
            )

        else:

            self.inventory[name].quantity += quantity

        return True

    def remove_item(
        self,
        name: str,
        quantity: float = 1.0,
    ) -> bool:

        if name not in self.inventory:
            return False

        item = self.inventory[name]

        if item.quantity < quantity:
            return False

        item.quantity -= quantity

        if item.quantity <= 0:
            del self.inventory[name]

        return True

    def has_item(
        self,
        name: str,
        quantity: float = 1.0,
    ) -> bool:

        if name not in self.inventory:
            return False

        return self.inventory[name].quantity >= quantity

    def clear_inventory(
        self,
    ) -> None:

        self.inventory.clear()

    # ========================================================
    # Task Management
    # ========================================================

    def assign_task(
        self,
        task: Any,
    ) -> None:

        self.current_task = task

        self.busy = True

        self.state = AgentState.WORKING
        self.current_activity = "Working"

    def queue_task(
        self,
        task: Any,
    ) -> None:

        self.task_queue.append(task)

    def next_task(
        self,
    ) -> Any | None:

        if not self.task_queue:
            return None

        return self.task_queue.pop(0)

    def complete_task(
        self,
    ) -> None:

        if self.current_task is None:
            return

        self.tasks_completed += 1

        self.current_task = None

        self.busy = False

        if self.task_queue:

            self.assign_task(self.next_task())

        else:

            self.state = AgentState.IDLE
            self.current_activity = "Idle"

    def cancel_task(
        self,
    ) -> None:

        self.current_task = None

        self.busy = False

        self.state = AgentState.IDLE

    # ========================================================
    # Health
    # ========================================================

    def take_damage(
        self,
        amount: float,
    ) -> None:

        if not self.alive:
            return

        self.health = max(
            0.0,
            self.health - amount,
        )

        if self.health <= 0:

            self.alive = False

            self.state = AgentState.DEAD

        else:

            self.state = AgentState.INJURED
        self.current_activity = "Injured"

    def heal(
        self,
        amount: float,
    ) -> None:

        if not self.alive:
            return

        self.health = min(
            self.max_health,
            self.health + amount,
        )

        if self.state == AgentState.INJURED:

            self.state = AgentState.IDLE

    # ========================================================
    # Needs
    # ========================================================

    def consume_oxygen(
        self,
        amount: float,
    ) -> None:

        self.oxygen = max(
            0.0,
            self.oxygen - amount,
        )

        if self.oxygen <= 0:

            self.take_damage(5)

    def refill_oxygen(
        self,
        amount: float = 100.0,
    ) -> None:

        self.oxygen = min(
            100.0,
            self.oxygen + amount,
        )

    def eat(
        self,
        nutrition: float = 20.0,
    ) -> None:

        self.hunger = max(
            0.0,
            self.hunger - nutrition,
        )

        self.state = AgentState.EATING
        self.current_activity = "Eating"

    def drink(
        self,
        hydration: float = 20.0,
    ) -> None:

        self.thirst = max(
            0.0,
            self.thirst - hydration,
        )

        self.state = AgentState.DRINKING
        self.current_activity = "Drinking"

    def sleep(
        self,
        recovery: float = 25.0,
    ) -> None:

        self.fatigue = max(
            0.0,
            self.fatigue - recovery,
        )

        self.stress = max(
            0.0,
            self.stress - 5,
        )

        self.state = AgentState.SLEEPING
        self.current_activity = "Sleeping"

    def rest(
        self,
        amount: float = 10.0,
    ) -> None:

        self.fatigue = max(
            0.0,
            self.fatigue - amount,
        )

        self.state = AgentState.IDLE
        self.current_activity = "Resting"

    def change_morale(
        self,
        amount: float,
    ) -> None:

        self.morale = max(
            0.0,
            min(
                100.0,
                self.morale + amount,
            ),
        )

    def change_stress(
        self,
        amount: float,
    ) -> None:

        self.stress = max(
            0.0,
            min(
                100.0,
                self.stress + amount,
            ),
        )

        # ========================================================

    # Update Loop
    # ========================================================

    def step(
        self,
    ) -> None:
        """
        Called every simulation tick.
        """

        if not self.alive:
            return

        if self.moving:
            self.follow_path()

    def hourly_update(
        self,
        needs_intensity: float = 1.0,
    ) -> None:
        """
        Called once every simulation hour.
        """

        if not self.alive:
            return

        self.hours_alive += 1

        if self.busy:
            self.hours_worked += 1

        needs_intensity = max(0.0, needs_intensity)
        self.consume_oxygen(0.5 * needs_intensity)

        self.hunger = min(
            100.0,
            self.hunger + 1.0 * needs_intensity,
        )

        self.thirst = min(
            100.0,
            self.thirst + 1.5 * needs_intensity,
        )

        self.fatigue = min(
            100.0,
            self.fatigue + 0.75 * needs_intensity,
        )
        self.social_need = min(100.0, self.social_need + 2.0 * needs_intensity)
        self.recreation_need = min(100.0, self.recreation_need + 1.0 * needs_intensity)

        if self.stress > 80:

            self.change_morale(-0.5)

        if self.hunger >= 100:

            self.take_damage(0.5)

        if self.thirst >= 100:

            self.take_damage(1.0)

        if self.fatigue >= 100:

            self.change_stress(1.0)

        if self.social_need >= 85:
            self.change_stress(.5)

    def daily_update(
        self,
    ) -> None:
        """
        Called once every simulation day.
        """

        if not self.alive:
            return

        self.change_stress(-2)

        if self.morale < 25:

            self.change_stress(5)

        if self.social_need < 35 and self.recreation_need < 40:
            self.change_morale(.25)
        elif self.social_need >= 85 or self.recreation_need >= 90:
            self.change_morale(-.5)

        if self.health < self.max_health:

            self.heal(0.5)

    # ========================================================
    # Runtime Helpers
    # ========================================================

    def revive(
        self,
    ) -> None:

        self.alive = True

        self.health = self.max_health

        self.state = AgentState.IDLE

    def teleport(
        self,
        position: tuple[int, int],
    ) -> None:

        self.position = position

        self.destination = None

        self.path.clear()

        self.moving = False

    def reset_needs(
        self,
    ) -> None:

        self.oxygen = 100.0

        self.hunger = 0.0

        self.thirst = 0.0

        self.fatigue = 0.0

        self.stress = 0.0

        self.morale = 100.0

    def clear_tasks(
        self,
    ) -> None:

        self.current_task = None

        self.task_queue.clear()

        self.busy = False

        self.state = AgentState.IDLE

    # ========================================================
    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict[str, Any]:

        data = asdict(self)

        data["state"] = self.state.value

        data["inventory"] = {
            name: {
                "quantity": item.quantity,
                "weight": item.weight,
            }
            for name, item in self.inventory.items()
        }

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict[str, Any],
    ) -> "BaseAgent":

        inventory = {}

        for name, values in data.pop(
            "inventory",
            {},
        ).items():

            inventory[name] = InventoryItem(
                name=name,
                quantity=values["quantity"],
                weight=values["weight"],
            )

        state = AgentState(data.pop("state"))

        agent = cls(
            **data,
        )

        agent.inventory = inventory

        agent.state = state

        return agent

        # ========================================================

    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict[str, Any]:

        return {
            "id": self.unique_id,
            "name": self.name,
            "profession": self.profession,
            "state": self.state.value,
            "alive": self.alive,
            "position": self.position,
            "destination": self.destination,
            "moving": self.moving,
            "outside": self.outside,
            "health": round(
                self.health,
                2,
            ),
            "max_health": round(
                self.max_health,
                2,
            ),
            "oxygen": round(
                self.oxygen,
                2,
            ),
            "hunger": round(
                self.hunger,
                2,
            ),
            "thirst": round(
                self.thirst,
                2,
            ),
            "fatigue": round(
                self.fatigue,
                2,
            ),
            "stress": round(
                self.stress,
                2,
            ),
            "morale": round(
                self.morale,
                2,
            ),
            "inventory_items": len(
                self.inventory,
            ),
            "inventory_weight": round(
                self.carrying_weight,
                2,
            ),
            "busy": self.busy,
            "current_task": (
                None if self.current_task is None else str(self.current_task)
            ),
            "queued_tasks": len(
                self.task_queue,
            ),
            "priority": self.priority,
            "distance_travelled": round(
                self.distance_travelled,
                2,
            ),
            "tasks_completed": self.tasks_completed,
            "hours_worked": self.hours_worked,
            "hours_alive": self.hours_alive,
            "personality": dict(self.personality),
            "appearance": dict(self.appearance),
            "background": self.background,
            "employment_status": self.employment_status,
            "work_schedule": dict(self.work_schedule),
            "workplace_id": self.workplace_id,
            "current_activity": self.current_activity,
            "next_activity": self.next_activity,
            "decision_reason": self.decision_reason,
            "activity_until_tick": self.activity_until_tick,
            "social_need": round(self.social_need, 2),
            "recreation_need": round(self.recreation_need, 2),
        }

    # ========================================================
    # Utility
    # ========================================================

    def distance_to(
        self,
        position: tuple[int, int],
    ) -> float:

        return dist(
            self.position,
            position,
        )

    def at_destination(
        self,
    ) -> bool:

        if self.destination is None:

            return True

        return self.position == self.destination

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.metadata[key] = value

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.metadata.get(
            key,
            default,
        )

    def clear_metadata(
        self,
    ) -> None:

        self.metadata.clear()

    def __repr__(
        self,
    ) -> str:

        return (
            "BaseAgent("
            f"id={self.unique_id}, "
            f"name='{self.name}', "
            f"profession='{self.profession}', "
            f"state='{self.state.value}', "
            f"health={self.health:.1f}, "
            f"position={self.position}"
            ")"
        )

    # ===========================
    # END OF FILE
    # ===========================


# Canonical alias used throughout the project.
Agent = BaseAgent
