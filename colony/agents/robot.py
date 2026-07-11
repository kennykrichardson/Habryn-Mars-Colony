"""
robot.py

Part 1/4

Canonical Robot implementation.

Inheritance

BaseAgent
    └── Robot

Every autonomous machine in Habryn inherits from Robot.

BuilderBot
RepairBot
MiningBot
CargoBot
ExplorationBot
MedicalBot
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .base_agent import BaseAgent, AgentState

# ============================================================
# Robot Status
# ============================================================


class RobotStatus(Enum):

    STANDBY = "Standby"

    ACTIVE = "Active"

    CHARGING = "Charging"

    MAINTENANCE = "Maintenance"

    OFFLINE = "Offline"


# ============================================================
# Robot
# ============================================================


@dataclass
class Robot(BaseAgent):

    model: str = "MK-I"

    serial_number: str = ""

    robot_status: RobotStatus = RobotStatus.STANDBY

    battery_level: float = 100.0

    battery_capacity: float = 100.0

    durability: float = 100.0

    firmware_version: str = "1.0.0"

    efficiency: float = 1.0

    tools: list[str] = field(default_factory=list)

    diagnostics: dict[str, float] = field(default_factory=dict)

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        super().__post_init__()

        self.profession = "Robot"

        self.hunger = 0.0

        self.thirst = 0.0

        self.fatigue = 0.0

        self.stress = 0.0

        self.morale = 100.0

        self.diagnostics.setdefault(
            "motors",
            100.0,
        )

        self.diagnostics.setdefault(
            "cpu",
            100.0,
        )

        self.diagnostics.setdefault(
            "battery",
            100.0,
        )

    # ========================================================
    # Battery
    # ========================================================

    def consume_battery(
        self,
        amount: float,
    ) -> None:

        self.battery_level = max(
            0.0,
            self.battery_level - amount,
        )

        if self.battery_level <= 0:

            self.robot_status = RobotStatus.OFFLINE

            self.state = AgentState.IDLE

    def recharge(
        self,
        amount: float = 100.0,
    ) -> None:

        self.robot_status = RobotStatus.CHARGING

        self.battery_level = min(
            self.battery_capacity,
            self.battery_level + amount,
        )

        if self.battery_level >= 100:

            self.robot_status = RobotStatus.ACTIVE

    # ========================================================
    # Maintenance
    # ========================================================

    def maintenance(
        self,
        amount: float = 5.0,
    ) -> None:

        self.robot_status = RobotStatus.MAINTENANCE

        self.durability = min(
            100.0,
            self.durability + amount,
        )

        for component in self.diagnostics:

            self.diagnostics[component] = min(
                100.0,
                self.diagnostics[component] + amount,
            )

        self.robot_status = RobotStatus.ACTIVE

        # ========================================================

    # Tools
    # ========================================================

    def install_tool(
        self,
        tool: str,
    ) -> None:

        if tool not in self.tools:

            self.tools.append(
                tool,
            )

    def uninstall_tool(
        self,
        tool: str,
    ) -> None:

        if tool in self.tools:

            self.tools.remove(
                tool,
            )

    def has_tool(
        self,
        tool: str,
    ) -> bool:

        return tool in self.tools

    # ========================================================
    # Diagnostics
    # ========================================================

    def damage_component(
        self,
        component: str,
        amount: float,
    ) -> None:

        self.diagnostics.setdefault(
            component,
            100.0,
        )

        self.diagnostics[component] = max(
            0.0,
            self.diagnostics[component] - amount,
        )

        self.durability = max(
            0.0,
            self.durability - (amount * 0.25),
        )

    def repair_component(
        self,
        component: str,
        amount: float,
    ) -> None:

        self.diagnostics.setdefault(
            component,
            100.0,
        )

        self.diagnostics[component] = min(
            100.0,
            self.diagnostics[component] + amount,
        )

    def diagnostic_report(
        self,
    ) -> dict[str, float]:

        return dict(
            self.diagnostics,
        )

    # ========================================================
    # Updates
    # ========================================================

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

        self.consume_battery(
            0.5,
        )

        if self.busy:

            self.consume_battery(
                1.0,
            )

        self.durability = max(
            0.0,
            self.durability - 0.01,
        )

        if self.battery_level < 20:

            self.robot_status = RobotStatus.CHARGING

        elif self.robot_status == RobotStatus.CHARGING:

            self.robot_status = RobotStatus.ACTIVE

    def daily_update(
        self,
    ) -> None:

        self.durability = max(
            0.0,
            self.durability - 0.05,
        )

        for component in self.diagnostics:

            self.diagnostics[component] = max(
                0.0,
                self.diagnostics[component] - 0.02,
            )

        # ========================================================

    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data["robot_status"] = self.robot_status.value

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "Robot":

        robot_status = RobotStatus(
            data.pop(
                "robot_status",
            ),
        )

        robot = cls(
            **data,
        )

        robot.robot_status = robot_status

        return robot

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "model": self.model,
                "serial_number": self.serial_number,
                "robot_status": self.robot_status.value,
                "battery_level": round(
                    self.battery_level,
                    2,
                ),
                "battery_capacity": round(
                    self.battery_capacity,
                    2,
                ),
                "durability": round(
                    self.durability,
                    2,
                ),
                "firmware_version": self.firmware_version,
                "efficiency": round(
                    self.efficiency,
                    2,
                ),
                "tools": list(
                    self.tools,
                ),
                "diagnostics": dict(
                    self.diagnostics,
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
            "Robot("
            f"id={self.unique_id}, "
            f"name='{self.name}', "
            f"model='{self.model}', "
            f"battery={self.battery_level:.1f}%, "
            f"status='{self.robot_status.value}'"
            ")"
        )

    # ============================================================
    # Canonical Alias
    # ============================================================


Machine = Robot
