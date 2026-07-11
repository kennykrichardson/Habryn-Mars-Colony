"""
ai_manager.py

Part 1/4

Canonical AI Manager.

Responsible for colony-wide decision making.

Owns

- agent registration
- resource registration
- alert level
- task recommendations
- colony health evaluation

Does NOT perform work.

Agents perform work.
TaskManager assigns work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from colony.systems.base_manager import BaseManager

# ============================================================
# Alert Level
# ============================================================


class AlertLevel(Enum):

    GREEN = "Green"

    YELLOW = "Yellow"

    ORANGE = "Orange"

    RED = "Red"

    CRITICAL = "Critical"


# ============================================================
# AI Manager
# ============================================================


@dataclass
class AIManager(BaseManager):

    name: str = "AI Manager"

    agents: dict[int, Any] = field(default_factory=dict)

    resources: dict[str, Any] = field(default_factory=dict)

    buildings: dict[int, Any] = field(default_factory=dict)

    alert_level: AlertLevel = AlertLevel.GREEN

    colony_score: float = 100.0

    recommendations: list[str] = field(default_factory=list)

    # ========================================================
    # Registration
    # ========================================================

    def register_agent(
        self,
        agent: Any,
    ) -> None:

        self.agents[agent.unique_id] = agent

    def unregister_agent(
        self,
        agent: Any,
    ) -> None:

        self.agents.pop(
            agent.unique_id,
            None,
        )

    def register_resource(
        self,
        name: str,
        resource: Any,
    ) -> None:

        self.resources[name] = resource

    def register_building(
        self,
        building: Any,
    ) -> None:

        self.buildings[building.building_id] = building

        # ========================================================

    # Colony Evaluation
    # ========================================================

    def evaluate_resources(
        self,
    ) -> None:

        if not self.resources:

            return

        percentages = []

        for resource in self.resources.values():

            if hasattr(
                resource,
                "fill_percentage",
            ):

                percentages.append(resource.fill_percentage)

        if not percentages:

            return

        self.colony_score = sum(percentages) / len(percentages)

        self._update_alert_level()

    def evaluate_buildings(
        self,
    ) -> None:

        if not self.buildings:

            return

        damaged = 0

        for building in self.buildings.values():

            if getattr(
                building,
                "needs_maintenance",
                False,
            ):

                damaged += 1

        if damaged > 5:

            self.recommend(
                "Schedule maintenance crews.",
            )

    # ========================================================
    # Alert Level
    # ========================================================

    def _update_alert_level(
        self,
    ) -> None:

        score = self.colony_score

        if score >= 80:

            self.alert_level = AlertLevel.GREEN

        elif score >= 60:

            self.alert_level = AlertLevel.YELLOW

        elif score >= 40:

            self.alert_level = AlertLevel.ORANGE

        elif score >= 20:

            self.alert_level = AlertLevel.RED

        else:

            self.alert_level = AlertLevel.CRITICAL

    # ========================================================
    # Recommendations
    # ========================================================

    def recommend(
        self,
        message: str,
    ) -> None:

        if message not in self.recommendations:

            self.recommendations.append(
                message,
            )

    def clear_recommendations(
        self,
    ) -> None:

        self.recommendations.clear()

        # ========================================================

    # Update Loop
    # ========================================================

    def step(
        self,
    ) -> None:

        super().step()

        self.evaluate_resources()

        self.evaluate_buildings()

    def hourly_update(
        self,
    ) -> None:

        super().hourly_update()

        self.evaluate_resources()

        self.evaluate_buildings()

    def daily_update(
        self,
    ) -> None:

        super().daily_update()

        self.evaluate_resources()

        self.evaluate_buildings()

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:

        stats = super().statistics()

        stats.update(
            {
                "agents": len(
                    self.agents,
                ),
                "resources": len(
                    self.resources,
                ),
                "buildings": len(
                    self.buildings,
                ),
                "alert_level": self.alert_level.value,
                "colony_score": round(
                    self.colony_score,
                    2,
                ),
                "recommendations": len(
                    self.recommendations,
                ),
            }
        )

        return stats

    # ========================================================
    # Utility
    # ========================================================

    def clear(
        self,
    ) -> None:

        self.agents.clear()

        self.resources.clear()

        self.buildings.clear()

        self.recommendations.clear()

    def __repr__(
        self,
    ) -> str:

        return (
            "AIManager("
            f"agents={len(self.agents)}, "
            f"resources={len(self.resources)}, "
            f"buildings={len(self.buildings)}, "
            f"alert='{self.alert_level.value}'"
            ")"
        )

        # ========================================================

    # Serialization
    # ========================================================

    def serialize(
        self,
    ) -> dict:

        data = super().serialize()

        data.update(
            {
                "alert_level": self.alert_level.value,
                "colony_score": self.colony_score,
                "recommendations": list(
                    self.recommendations,
                ),
            }
        )

        return data

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> "AIManager":

        manager = cls()

        manager.enabled = data.get(
            "enabled",
            True,
        )

        manager.initialized = data.get(
            "initialized",
            False,
        )

        manager.tick_count = data.get(
            "tick_count",
            0,
        )

        manager.hour_count = data.get(
            "hour_count",
            0,
        )

        manager.day_count = data.get(
            "day_count",
            0,
        )

        manager.update_count = data.get(
            "update_count",
            0,
        )

        manager.error_count = data.get(
            "error_count",
            0,
        )

        manager.alert_level = AlertLevel(
            data.get(
                "alert_level",
                AlertLevel.GREEN.value,
            )
        )

        manager.colony_score = data.get(
            "colony_score",
            100.0,
        )

        manager.recommendations = list(
            data.get(
                "recommendations",
                [],
            )
        )

        return manager


# ============================================================
# Canonical Alias
# ============================================================

ColonyAI = AIManager
