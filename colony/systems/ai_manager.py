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
import importlib
import re
from typing import Any

from colony.systems.base_manager import BaseManager
from colony.tasks.task import BaseTask, TaskPriority

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

    # Hourly, authoritative planning state. Histories are deliberately bounded so
    # long-running colonies do not grow their save files without limit.
    last_resource_amounts: dict[str, float] = field(default_factory=dict)
    resource_forecasts: dict[str, dict[str, Any]] = field(default_factory=dict)
    goals: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    planning_interval_hours: int = 1
    last_planning_tick: int = -1

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

    def assess_and_plan(self, model: Any) -> None:
        """Forecast colony reserves and create deduplicated, executable work."""
        tick = model.scheduler.tick
        if self.last_planning_tick >= 0 and tick - self.last_planning_tick < max(
            1, self.planning_interval_hours * model.scheduler.ticks_per_hour
        ):
            return
        self.last_planning_tick = tick
        next_amounts: dict[str, float] = {}
        forecasts: dict[str, dict[str, Any]] = {}
        goals: list[dict[str, Any]] = []
        expansion_queued = False
        protected_resources = {"Food", "Water", "Oxygen", "Power", "Fuel"}
        fuel_depot = next((building for building in model.buildings_by_id.values()
                           if type(building).__name__ == "FuelDepot"), None)
        fuel_target = float(getattr(fuel_depot, "target_reserve", 0.0))
        for name, resource in sorted(model.resource_manager.resources.items()):
            amount = float(resource.current_amount)
            previous = self.last_resource_amounts.get(name, amount)
            net_change = amount - previous
            hours_to_empty = amount / -net_change if net_change < -1e-9 else None
            fill = float(resource.fill_percentage)
            target_shortfall = name == "Fuel" and fuel_target > 0 and amount < fuel_target
            if name in protected_resources and (
                fill <= 10 or (hours_to_empty is not None and hours_to_empty <= 12) or target_shortfall
            ):
                severity = "critical" if fill <= 10 or (hours_to_empty is not None and hours_to_empty <= 4) else "projected"
                reason = (f"{name} has {amount:.1f} {resource.unit} ({fill:.0f}% capacity); "
                          + (f"at the observed net rate it may run out in {hours_to_empty:.1f} h."
                             if hours_to_empty is not None else "reserves are below the safety threshold."))
                self._record_decision(f"Protect {name} reserves", reason, tick)
                goal = {"id": f"reserve:{name}", "title": f"Protect {name} reserves",
                        "priority": 5 if severity == "critical" else 4,
                        "status": "active", "severity": severity, "reason": reason}
                if ((hours_to_empty is not None and hours_to_empty <= 4 or amount <= 0.0)
                        and model.autonomy_manager.enabled and not expansion_queued):
                    building_name = {"Water": "WaterPlant", "Oxygen": "OxygenGenerator",
                                     "Food": "Greenhouse", "Power": "SolarArray"}.get(name)
                    if building_name:
                        project, blocker = self._plan_capacity(model, building_name)
                        if project is not None:
                            expansion_queued = True
                            goal["status"] = "planned"
                            goal["reason"] = (reason + f" AI queued {building_name} at {project.position}; "
                                               "construction requires an engineer, power, and materials.")
                            self._record_decision(f"Expand {name} production",
                                                  goal["reason"], tick)
                        elif blocker:
                            goal["status"] = "blocked"
                            goal["reason"] = reason + " Expansion blocked: " + blocker
                            self._record_decision(f"{name} expansion blocked", goal["reason"], tick)
                goals.append(goal)
                if (name == "Fuel" and model.autonomy_manager.enabled
                        and (fill <= 10 or (hours_to_empty is not None and hours_to_empty <= 12)
                             or target_shortfall)
                        and not self._has_goal_task(model, "fuel_harvest")):
                    deposits = [(model.mars_map.resource_amount(*item["position"], "Fuel"),
                                 tuple(item["position"]))
                                for item in model.discovered_deposits if item["resource"] == "Fuel"
                                and model.mars_map.resource_amount(*item["position"], "Fuel") > 0.0]
                    if deposits:
                        available, position = max(deposits)
                        amount = min(20.0, available, resource.storage_capacity - amount,
                                     max(0.0, fuel_target - amount) if fuel_target else float("inf"),
                                     max(0.0, fuel_depot.maximum_stock - amount)
                                     if fuel_depot is not None and fuel_depot.maximum_stock else float("inf"))
                        if amount > 0:
                            try:
                                model.create_fuel_harvest_task(position, amount)
                            except ValueError as error:
                                reason = f"Fuel recovery is blocked: {error}."
                                self._record_decision("Fuel recovery blocked", reason, tick)
                                goals.append({"id": "fuel-harvest", "title": "Recover fuel reserves",
                                              "priority": 5, "status": "blocked", "reason": reason})
                            else:
                                reason = f"Recover {amount:g} L from a finite mapped deposit and deliver it to storage."
                                self._record_decision("Recover fuel reserves", reason, tick)
                                goals.append({"id": "fuel-harvest", "title": "Recover fuel reserves",
                                              "priority": 5, "status": "planned", "reason": reason})
            forecasts[name] = {"amount": round(amount, 3), "capacity": float(resource.storage_capacity),
                               "fill_percentage": round(fill, 2), "net_change_per_hour": round(net_change, 3),
                               "hours_until_empty": (round(hours_to_empty, 1)
                                                     if hours_to_empty is not None else None)}
            next_amounts[name] = amount
        self.last_resource_amounts = next_amounts
        self.resource_forecasts = forecasts

        explorers = [agent for agent in model.agents_by_id.values()
                     if getattr(agent, "role", None) == "exploration" and agent.alive]
        if explorers and model.autonomy_manager.enabled and not self._has_goal_task(model, "explore"):
            targets = []
            for rover in explorers:
                if rover.battery_level <= 25:
                    continue
                frontier = sorted(
                    ((abs(position[0] - rover.position[0]) + abs(position[1] - rover.position[1]), position)
                     for position, tile in model.mars_map.tiles.items()
                     if not tile.explored and tile.walkable),
                    key=lambda item: (item[0], item[1][1], item[1][0]))
                for distance, position in frontier[:32]:
                    path = model._path_for(tuple(rover.position), position)
                    if path and len(path) * .12 + 20 < rover.battery_level:
                        targets.append((len(path), rover.unique_id, position, rover))
                        break
            if targets:
                _distance, _rover_id, position, rover = min(targets)
                task = BaseTask(name=f"Survey terrain near {position[0]},{position[1]}",
                                description="Explore an unknown region and register discovered deposits.",
                                priority=TaskPriority.NORMAL, duration=1, location=position,
                                metadata={"action": "explore", "required_role": "exploration",
                                          "radius": 2, "work_energy": 2.0})
                task.task_id = f"explore-{tick}-{rover.unique_id}-{position[0]}-{position[1]}"
                model.task_manager.register_task(task)
                reason = f"Assign an exploration rover to survey the unexplored tile at {position}."
                self._record_decision("Survey unexplored terrain", reason, tick)
                goals.append({"id": "exploration:frontier", "title": "Survey unexplored terrain",
                              "priority": 2, "status": "planned", "reason": reason,
                              "rover": rover.name, "position": position})

        # Maintenance is actionable only when the registered worker can travel to
        # the facility. Keep the manager request as the single source of truth.
        for request in tuple(model.maintenance_manager.pending_requests()):
            building = request.building
            if building is None or getattr(request, "assigned_agent", None) is not None:
                continue
            if self._has_goal_task(model, "maintenance", building.building_id):
                continue
            location = model._building_entry(building)
            if location is None:
                reason = f"Cannot maintain {building.name}: no walkable access tile exists."
                self._record_decision("Maintenance blocked", reason, tick)
                goals.append({"id": f"maintenance:{building.building_id}", "title": f"Maintain {building.name}",
                              "priority": request.priority, "status": "blocked", "reason": reason})
                continue
            task = BaseTask(name=f"Maintain {building.name}",
                            description=f"Restore maintenance and integrity at {building.name}.",
                            priority=TaskPriority.CRITICAL if request.priority >= 4 else TaskPriority.HIGH,
                            duration=4, target=building, location=location,
                            required_skills={"engineering": 1},
                            metadata={"action": "maintenance", "ai_goal_id": f"maintenance:{building.building_id}",
                                      "repair_amount": request.repair_amount})
            model.task_manager.register_task(task)
            reason = f"{building.name} needs maintenance; an engineer can reach the facility."
            self._record_decision(f"Assign maintenance: {building.name}", reason, tick)
            goals.append({"id": f"maintenance:{building.building_id}", "title": f"Maintain {building.name}",
                          "priority": request.priority, "status": "planned", "reason": reason})

        # Crop care is triggered by actual crop condition and only requested from
        # qualified farmers; the task's work step consumes colony water.
        for greenhouse in sorted(model.buildings_by_id.values(), key=lambda item: item.building_id):
            if type(greenhouse).__name__ != "Greenhouse" or greenhouse.crop_health >= 70:
                continue
            goal_id = f"crop-care:{greenhouse.building_id}"
            if self._has_goal_task(model, "farm_water", greenhouse.building_id):
                continue
            location = model._building_entry(greenhouse)
            if location is None:
                continue
            water = model.resource_manager.amount("Water")
            if water < 2.0:
                reason = f"{greenhouse.name} crop health is {greenhouse.crop_health:.0f}%; watering is blocked by insufficient water."
                goals.append({"id": goal_id, "title": f"Recover {greenhouse.name} crops", "priority": 4,
                              "status": "blocked", "reason": reason})
                self._record_decision("Crop recovery blocked", reason, tick)
                continue
            task = BaseTask(name=f"Water crops in {greenhouse.name}",
                            description="Greenhouse crop care and irrigation.", priority=TaskPriority.HIGH,
                            duration=2, target=greenhouse, location=location,
                            required_skills={"agriculture": 1},
                            metadata={"action": "farm_water", "ai_goal_id": goal_id, "water_cost": 2.0})
            model.task_manager.register_task(task)
            reason = f"Crop health is {greenhouse.crop_health:.0f}%; assign a farmer to irrigate using stored water."
            self._record_decision(f"Recover {greenhouse.name} crops", reason, tick)
            goals.append({"id": goal_id, "title": f"Recover {greenhouse.name} crops", "priority": 4,
                          "status": "planned", "reason": reason})
        self.goals = goals[-40:]

    @staticmethod
    def _plan_capacity(model: Any, building_name: str) -> tuple[Any | None, str | None]:
        """Use the normal construction API for a single bounded capacity response."""
        module = importlib.import_module(
            f"colony.buildings.{re.sub(r'(?<!^)(?=[A-Z])', '_', building_name).lower()}"
        )
        footprint = getattr(module, building_name).default_footprint
        existing = sum(type(item).__name__ == building_name for item in model.buildings_by_id.values())
        projects = list(model.construction_manager.construction_queue) + list(model.construction_manager.active_projects)
        committed = sum(project.building_name == building_name for project in projects)
        if existing + committed >= 2:
            return None, f"the colony already has {existing} {building_name} facilities."
        if building_name != "SolarArray":
            power = model.resource_manager.resource("Power")
            if power is None or power.fill_percentage < 10:
                return None, "power reserves are too low to add a powered facility safely."
        anchor = next((tuple(item.position) for item in model.buildings_by_id.values()
                       if type(item).__name__ == "Habitat"), (model.mars_map.width // 2,
                                                               model.mars_map.height // 2))
        radius = min(10, max(model.mars_map.width, model.mars_map.height))
        candidates = [(anchor[0] + dx, anchor[1] + dy)
                      for distance in range(1, radius + 1)
                      for dy in range(-distance, distance + 1)
                      for dx in range(-distance, distance + 1)
                      if max(abs(dx), abs(dy)) == distance]
        last_error = "no buildable site is available near the settlement."
        for position in candidates:
            try:
                project = model.queue_construction(building_name, position, priority=5)
                project.footprint = footprint
                return project, None
            except (ValueError, IndexError) as error:
                last_error = str(error)
        return None, last_error

    def _has_goal_task(self, model: Any, action: str, building_id: int | None = None) -> bool:
        if action in {"fuel_harvest", "explore"}:
            return any(task.metadata.get("action") == action
                       for task in model.task_manager.tasks)
        goal_id = f"maintenance:{building_id}" if action == "maintenance" else f"crop-care:{building_id}"
        return any(task.metadata.get("ai_goal_id") == goal_id
                   for task in (*model.task_manager.tasks, *model.task_manager.active_tasks()))

    def _record_decision(self, decision: str, reason: str, tick: int) -> None:
        item = {"tick": tick, "decision": decision, "reason": reason}
        if not self.decisions or self.decisions[-1] != item:
            self.decisions.append(item)
            self.decisions[:] = self.decisions[-100:]

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
                "active_goals": sum(goal.get("status") == "planned" for goal in self.goals),
                "blocked_goals": sum(goal.get("status") == "blocked" for goal in self.goals),
                "forecasts": len(self.resource_forecasts),
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
        self.last_resource_amounts.clear()
        self.resource_forecasts.clear()
        self.goals.clear()
        self.decisions.clear()

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
                "last_resource_amounts": dict(self.last_resource_amounts),
                "resource_forecasts": {key: dict(value) for key, value in self.resource_forecasts.items()},
                "goals": [dict(goal) for goal in self.goals],
                "decisions": [dict(decision) for decision in self.decisions],
                "planning_interval_hours": self.planning_interval_hours,
                "last_planning_tick": self.last_planning_tick,
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
        manager.last_resource_amounts = {str(key): float(value)
                                          for key, value in data.get("last_resource_amounts", {}).items()}
        manager.resource_forecasts = {str(key): dict(value)
                                      for key, value in data.get("resource_forecasts", {}).items()}
        manager.goals = [dict(value) for value in data.get("goals", ())]
        manager.decisions = [dict(value) for value in data.get("decisions", ())][-100:]
        manager.planning_interval_hours = max(1, int(data.get("planning_interval_hours", 1)))
        manager.last_planning_tick = int(data.get("last_planning_tick", -1))

        return manager


# ============================================================
# Canonical Alias
# ============================================================

ColonyAI = AIManager
