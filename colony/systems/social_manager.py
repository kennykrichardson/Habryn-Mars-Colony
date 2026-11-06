"""Deterministic, bounded social relationships and contextual conversations."""
from __future__ import annotations

from dataclasses import dataclass, field
import random

from colony.systems.base_manager import BaseManager, ManagerState


@dataclass
class Relationship:
    first_id: int
    second_id: int
    familiarity: float = 0.0
    friendship: float = 0.0
    trust: float = 0.0
    respect: float = 0.0
    affinity: float = 0.0
    conflict: float = 0.0
    shared_work: int = 0

    @property
    def label(self) -> str:
        if self.conflict >= 55:
            return "Rival"
        if self.friendship >= 75 and self.trust >= 60:
            return "Close friend"
        if self.friendship >= 35:
            return "Friend"
        if self.familiarity >= 10:
            return "Acquaintance"
        return "Colleague"

    def to_dict(self) -> dict:
        return {name: getattr(self, name) for name in (
            "first_id", "second_id", "familiarity", "friendship", "trust", "respect",
            "affinity", "conflict", "shared_work")}


@dataclass
class Conversation:
    conversation_id: int
    participants: tuple[int, ...]
    topic: str
    context: str
    start_tick: int
    end_tick: int
    turns: list[dict] = field(default_factory=list)
    outcome: str = "In progress"
    active: bool = True

    def to_dict(self) -> dict:
        return {"conversation_id": self.conversation_id, "participants": list(self.participants),
                "topic": self.topic, "context": self.context, "start_tick": self.start_tick,
                "end_tick": self.end_tick, "turns": [dict(turn) for turn in self.turns],
                "outcome": self.outcome, "active": self.active}


@dataclass
class SocialManager(BaseManager):
    name: str = "Social Manager"
    seed: int = 42
    intensity: float = 1.0
    max_conversations: int = 200
    memory_limit: int = 20
    relationships: dict[str, Relationship] = field(default_factory=dict)
    conversations: list[Conversation] = field(default_factory=list)
    memories: dict[int, list[dict]] = field(default_factory=dict)
    cooldowns: dict[int, int] = field(default_factory=dict)
    next_conversation_id: int = 1
    interaction_count: int = 0
    _rng: random.Random = field(default_factory=random.Random, repr=False)

    def __post_init__(self):
        self._rng.seed(self.seed)

    @staticmethod
    def key(first_id: int, second_id: int) -> str:
        return f"{min(first_id, second_id)}:{max(first_id, second_id)}"

    def relationship(self, first_id: int, second_id: int) -> Relationship:
        key = self.key(first_id, second_id)
        if key not in self.relationships:
            self.relationships[key] = Relationship(min(first_id, second_id), max(first_id, second_id))
        return self.relationships[key]

    def set_seed(self, seed: int | None) -> None:
        self.seed = 0 if seed is None else int(seed)
        self._rng.seed(self.seed)

    def active_for(self, agent_id: int, tick: int | None = None) -> Conversation | None:
        for conversation in reversed(self.conversations):
            if conversation.active and agent_id in conversation.participants and (
                tick is None or tick < conversation.end_tick
            ):
                return conversation
        return None

    def recent_for(self, agent_id: int, limit: int = 4) -> list[dict]:
        return [conversation.to_dict() for conversation in self.conversations
                if agent_id in conversation.participants][-limit:]

    def update_hour(self, agents, tick: int, ticks_per_hour: int, context: dict) -> None:
        """Advance current dialogue and start at most one nearby conversation per hour."""
        by_id = {agent.unique_id: agent for agent in agents}
        active_ids: set[int] = set()
        for conversation in self.conversations:
            if not conversation.active:
                continue
            if tick >= conversation.end_tick:
                conversation.active = False
                conversation.outcome = "Collegial exchange"
                for participant_id in conversation.participants:
                    agent = by_id.get(participant_id)
                    if agent is not None and getattr(agent, "alive", True):
                        if agent.current_activity == "Socializing":
                            agent.current_activity = "Idle"
                            agent.state = type(agent.state).IDLE
                continue
            active_ids.update(conversation.participants)
            if tick >= conversation.start_tick + ticks_per_hour // 2 and len(conversation.turns) < 3:
                self._add_followup(conversation, by_id, context, tick)

        candidates = [agent for agent in agents if self.intensity > 0 and getattr(agent, "alive", True)
                      and "robot" not in type(agent).__name__.lower()
                      and agent.unique_id not in active_ids and not getattr(agent, "busy", False)
                      and not getattr(agent, "moving", False)
                      and getattr(agent, "social_need", 0) >= 45
                      and tick >= self.cooldowns.get(agent.unique_id, 0)
                      and str(getattr(agent, "current_activity", "")).lower() not in {"sleeping", "eating"}]
        candidates.sort(key=lambda a: (-a.social_need, a.unique_id))
        for index, first in enumerate(candidates):
            if first.unique_id in active_ids:
                continue
            possible = [other for other in candidates[index + 1:]
                        if other.unique_id not in active_ids
                        and abs(first.position[0] - other.position[0]) <= 1
                        and abs(first.position[1] - other.position[1]) <= 1]
            if not possible:
                continue
            second = possible[0]
            sociability = (first.personality.get("sociability", .5)
                           + second.personality.get("sociability", .5)) / 2
            introversion = (first.personality.get("introversion", .5)
                            + second.personality.get("introversion", .5)) / 2
            chance = min(.95, max(.1, (.22 + sociability * .5 - introversion * .15) * self.intensity))
            if self._rng.random() > chance:
                self.cooldowns[first.unique_id] = tick + ticks_per_hour
                continue
            self._start_conversation(first, second, tick, ticks_per_hour, context)
            active_ids.update((first.unique_id, second.unique_id))
            first.social_need = max(0.0, first.social_need - 24)
            second.social_need = max(0.0, second.social_need - 24)
            first.recreation_need = max(0.0, first.recreation_need - 8)
            second.recreation_need = max(0.0, second.recreation_need - 8)
            empathy = (first.personality.get("empathy", .5) + second.personality.get("empathy", .5)) / 2
            first.change_stress(-1.0 * empathy)
            second.change_stress(-1.0 * empathy)
            self.cooldowns[first.unique_id] = tick + ticks_per_hour * 3
            self.cooldowns[second.unique_id] = tick + ticks_per_hour * 3
            break

        self.interaction_count = sum(len(item.turns) for item in self.conversations)
        if len(self.conversations) > self.max_conversations:
            self.conversations = self.conversations[-self.max_conversations:]

    def _start_conversation(self, first, second, tick: int, ticks_per_hour: int, context: dict) -> None:
        topic, source = self._topic(first, second, context)
        pair = self.relationship(first.unique_id, second.unique_id)
        compatibility = 1.0 - sum(abs(first.personality.get(trait, .5) - second.personality.get(trait, .5))
                                  for trait in ("sociability", "empathy", "discipline")) / 3
        pair.familiarity = min(100.0, pair.familiarity + 5)
        pair.friendship = min(100.0, pair.friendship + max(0, 1 + compatibility * 2))
        pair.trust = min(100.0, pair.trust + 1.5 + first.personality.get("empathy", .5))
        pair.respect = min(100.0, pair.respect + 1.0)
        pair.affinity = min(100.0, pair.affinity + max(0, compatibility * 2))
        pair.shared_work += int(source == "shared work")
        conversation = Conversation(self.next_conversation_id,
                                    tuple(sorted((first.unique_id, second.unique_id))),
                                    topic, source, tick, tick + ticks_per_hour,
                                    outcome="Mutual support")
        self.next_conversation_id += 1
        self._add_turn(conversation, first, self._opening_line(first, topic, context), tick)
        self._add_turn(conversation, second, self._reply_line(second, topic, first), tick)
        self.conversations.append(conversation)
        for agent in (first, second):
            agent.current_activity = "Socializing"
            agent.state = type(agent.state).SOCIALIZING
            agent.next_activity = "Return to scheduled duties"
            agent.decision_reason = f"Social need was {agent.social_need:.0f}; nearby colleague available."
            memory = {"tick": tick, "kind": "conversation", "topic": topic,
                      "partner_id": second.unique_id if agent is first else first.unique_id,
                      "outcome": conversation.outcome}
            self.memories.setdefault(agent.unique_id, []).append(memory)
            self.memories[agent.unique_id] = self.memories[agent.unique_id][-self.memory_limit:]
            if hasattr(agent, "memories"):
                agent.memories.append(f"Sol {tick}: talked with {second.name if agent is first else first.name} about {topic}.")
                agent.memories[:] = agent.memories[-self.memory_limit:]
            if hasattr(agent, "relationships"):
                agent.relationships[second.unique_id if agent is first else first.unique_id] = pair.affinity

    def _topic(self, first, second, context: dict) -> tuple[str, str]:
        if context.get("warnings"):
            name = sorted(context["warnings"])[0].lower()
            return f"{name} reserves and colony safety", "resource alert"
        if context.get("events"):
            return "the latest colony event", "recent event"
        if first.current_task is not None and second.current_task is not None:
            return "today's shared work", "shared work"
        professions = {first.profession.lower(), second.profession.lower()}
        if "scientist" in professions:
            return "the latest research findings", "professional interests"
        if "farmer" in professions:
            return "greenhouse crops and the harvest", "professional interests"
        if "engineer" in professions:
            return "habitat systems and maintenance", "professional interests"
        if "medic" in professions:
            return "crew health and recovery", "professional interests"
        return "settlement life and the next sol", "social check-in"

    def _opening_line(self, agent, topic: str, context: dict) -> str:
        recent = self.memories.get(agent.unique_id, ())
        if recent and recent[-1].get("kind") == "conversation":
            remembered = recent[-1].get("topic", "our last shift")
            return f"I remember we talked about {remembered}. Has anything changed with {topic}?"
        if "alert" in topic:
            return f"Have you checked our {topic}? We should plan carefully."
        curiosity = agent.personality.get("curiosity", .5)
        if curiosity >= .65:
            return f"What have you learned about {topic}?"
        if agent.personality.get("sociability", .5) >= .65:
            return f"How are things with {topic}? I wanted to check in."
        return f"I've been thinking about {topic}. How is your shift going?"

    def _reply_line(self, agent, topic: str, first) -> str:
        if agent.profession == first.profession:
            return f"The {topic} work is moving along. We make a good team."
        if agent.personality.get("empathy", .5) >= .65:
            return f"Thanks for asking. Your {first.profession.lower()} perspective helps."
        return f"I can help with {topic} after my current duties."

    def _add_turn(self, conversation: Conversation, agent, text: str, tick: int) -> None:
        conversation.turns.append({"speaker_id": agent.unique_id, "speaker": agent.name,
                                   "text": text, "tick": tick})

    def _add_followup(self, conversation: Conversation, agents: dict, context: dict, tick: int) -> None:
        first_id, second_id = conversation.participants
        first, second = agents.get(first_id), agents.get(second_id)
        if first is None or second is None:
            conversation.active = False
            return
        speaker = second if len(conversation.turns) % 2 == 0 else first
        line = (f"Let's keep an eye on {conversation.topic}." if speaker.personality.get("discipline", .5) > .55
                else "We should talk again after the next shift.")
        self._add_turn(conversation, speaker, line, tick)

    def serialize(self) -> dict:
        data = {"name": self.name, "enabled": self.enabled, "initialized": self.initialized,
                "state": self.state.value, "tick_count": self.tick_count,
                "hour_count": self.hour_count, "day_count": self.day_count,
                "update_count": self.update_count, "error_count": self.error_count,
                "registry": dict(self.registry), "metadata": dict(self.metadata)}
        data.update({"seed": self.seed, "intensity": self.intensity,
                     "max_conversations": self.max_conversations, "memory_limit": self.memory_limit,
                     "relationships": {key: value.to_dict() for key, value in self.relationships.items()},
                     "conversations": [item.to_dict() for item in self.conversations],
                     "memories": {str(key): values[-self.memory_limit:] for key, values in self.memories.items()},
                     "cooldowns": {str(key): value for key, value in self.cooldowns.items()},
                     "next_conversation_id": self.next_conversation_id,
                     "interaction_count": self.interaction_count, "rng_state": self._rng.getstate()})
        return data

    def statistics(self) -> dict:
        data = super().statistics()
        data.update({"relationship_count": len(self.relationships),
                     "conversation_count": len(self.conversations),
                     "active_conversations": sum(item.active for item in self.conversations),
                     "dialogue_turns": self.interaction_count,
                     "memory_count": sum(len(items) for items in self.memories.values())})
        return data

    @classmethod
    def deserialize(cls, data: dict) -> "SocialManager":
        manager = cls(seed=data.get("seed", 42), intensity=data.get("intensity", 1.0),
                      max_conversations=data.get("max_conversations", 200),
                      memory_limit=data.get("memory_limit", 20))
        manager.state = ManagerState(data.get("state", ManagerState.STOPPED.value))
        manager.registry = dict(data.get("registry", {}))
        manager.metadata = dict(data.get("metadata", {}))
        for attr in ("enabled", "initialized", "tick_count", "hour_count", "day_count", "update_count", "error_count"):
            if attr in data:
                setattr(manager, attr, data[attr])
        manager.relationships = {key: Relationship(**value)
                                 for key, value in data.get("relationships", {}).items()}
        manager.conversations = [Conversation(
            item["conversation_id"], tuple(item["participants"]), item["topic"], item["context"],
            item["start_tick"], item["end_tick"], list(item.get("turns", [])),
            item.get("outcome", ""), item.get("active", False))
            for item in data.get("conversations", [])]
        manager.memories = {int(key): list(value)[-manager.memory_limit:]
                            for key, value in data.get("memories", {}).items()}
        manager.cooldowns = {int(key): value for key, value in data.get("cooldowns", {}).items()}
        manager.next_conversation_id = data.get("next_conversation_id", 1)
        manager.interaction_count = data.get("interaction_count", 0)
        if data.get("rng_state"):
            manager._rng.setstate(_nested_tuple(data["rng_state"]))
        return manager


def _nested_tuple(value):
    return tuple(_nested_tuple(item) if isinstance(item, list) else item for item in value)
