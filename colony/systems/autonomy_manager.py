"""Inspectable daily activity policy and profession-aware task scoring."""
from __future__ import annotations

from dataclasses import dataclass
from math import inf

from colony.systems.base_manager import BaseManager


@dataclass(frozen=True)
class ActivityDecision:
    action: str
    reason: str
    next_activity: str


@dataclass
class AutonomyManager(BaseManager):
    name: str = "Autonomy Manager"

    def decide(self, agent, hour: int, emergency: bool = False) -> ActivityDecision:
        if not getattr(agent, "alive", True):
            return ActivityDecision("inactive", "Character is incapacitated.", "Await recovery")
        if "robot" in type(agent).__name__.lower():
            if agent.battery_level <= 25:
                return ActivityDecision("recharge", "Battery reserve is low; return to a powered storage bank.",
                                        "Resume assigned robot work")
            if agent.durability <= 20:
                return ActivityDecision("maintenance", "Durability is critical; request maintenance.",
                                        "Resume assigned robot work")
            return ActivityDecision("work", "Robot is available for capability-matched work.", "Continue robot work")
        if agent.oxygen < 18 or agent.health < 20:
            return ActivityDecision("emergency", "Survival needs require immediate attention.", "Seek medical help")
        if agent.hunger >= 96 or agent.thirst >= 96:
            return ActivityDecision("emergency", "A critical personal need interrupts ordinary duties.",
                                    "Recover before returning to work")
        if emergency:
            return ActivityDecision("work", "A colony emergency overrides the regular schedule.", "Respond to emergency")
        schedule = getattr(agent, "work_schedule", {})
        sleep_hour = int(schedule.get("sleep_hour", 22)) % 24
        wake_hour = int(schedule.get("wake_hour", 6)) % 24
        sleeping_time = hour >= sleep_hour or hour < wake_hour if sleep_hour > wake_hour else sleep_hour <= hour < wake_hour
        if sleeping_time or agent.fatigue >= 85:
            return ActivityDecision("sleep", "Rest period or fatigue requires recovery.", "Return to scheduled duties")
        if agent.thirst >= 65:
            return ActivityDecision("drink", "Thirst is above the personal comfort threshold.", "Resume current objective")
        if agent.hunger >= 65:
            return ActivityDecision("eat", "Hunger is above the personal comfort threshold.", "Resume current objective")
        social_hour = int(schedule.get("social_hour", 19)) % 24
        social_window = abs(hour - social_hour) <= 1
        sociability = agent.personality.get("sociability", .5)
        social_threshold = 65 - sociability * 15
        if agent.social_need >= social_threshold and (social_window or agent.social_need >= 82):
            return ActivityDecision("socialize", "Social need is high and the schedule allows a break.", "Return to work")
        work_start = int(schedule.get("work_start", 8)) % 24
        work_end = int(schedule.get("work_end", 17)) % 24
        on_shift = work_start <= hour < work_end if work_start <= work_end else hour >= work_start or hour < work_end
        if on_shift:
            return ActivityDecision("work", "Within the character's scheduled work shift.", "Complete assigned work")
        if agent.recreation_need >= 72:
            return ActivityDecision("recreation", "Recreation need is high outside the work shift.", "Return to scheduled duties")
        return ActivityDecision("available", "Between scheduled activities.", "Next scheduled activity")

    def score_task(self, agent, task, distance: float, hour: int) -> tuple[float, str]:
        skills = getattr(agent, "skill_levels", {})
        required = getattr(task, "required_skills", {})
        if any(skills.get(skill, 0) < level for skill, level in required.items()):
            return -inf, "Required skill level is not met."
        priority = getattr(getattr(task, "priority", None), "value", 2)
        score = priority * 20.0 - distance * .8
        matches = {
            "engineer": ("repair", "maintenance", "power", "build", "inspect"),
            "scientist": ("research", "analy", "survey", "study", "science"),
            "farmer": ("crop", "greenhouse", "harvest", "plant", "water"),
            "medic": ("medical", "treat", "patient", "health", "injury"),
            "robot": ("transport", "haul", "rover", "robot", "explor"),
        }
        profession = str(getattr(agent, "profession", "")).lower()
        task_text = f"{task.name} {task.description}".lower()
        family = "robot" if "robot" in type(agent).__name__.lower() else profession
        skills_bonus = sum(min(10, skills.get(skill, 0)) for skill in required) * 2.5
        fit = any(word in task_text for word in matches.get(family, ()))
        score += skills_bonus + (22 if fit else 0)
        traits = getattr(agent, "personality", {})
        schedule = getattr(agent, "work_schedule", {})
        start, end = int(schedule.get("work_start", 8)), int(schedule.get("work_end", 17))
        on_shift = start <= hour < end if start <= end else hour >= start or hour < end
        score += traits.get("discipline", .5) * (8 if on_shift else -12)
        score += traits.get("ambition", .5) * 5
        score -= max(0, agent.fatigue - 55) * .35
        score -= max(0, agent.hunger - 55) * .5
        score -= max(0, agent.thirst - 55) * .6
        score -= max(0, agent.stress - 65) * .3
        reason = f"Priority {priority}; {profession or 'generalist'} suitability {'matches' if fit else 'is general'}; travel {distance:.0f} tiles."
        return score, reason

    def select_task(self, agent, tasks, model, hour: int):
        ranked = []
        for task in tasks:
            if task.location is None:
                distance = 0.0
            else:
                distance = agent.distance_to(task.location)
            score, reason = self.score_task(agent, task, distance, hour)
            if score > -inf and all(model.resource_manager.amount(name) >= amount
                                    for name, amount in task.required_resources.items()):
                ranked.append((score, -tasks.index(task), task, reason))
        if not ranked:
            return None, "No pending task matches current skills and resources."
        _score, _order, task, reason = max(ranked, key=lambda item: (item[0], item[1]))
        return task, reason
