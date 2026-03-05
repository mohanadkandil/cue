"""
Agent State Management

Handles:
- Loading agents from JSON
- Runtime state (sentiment, memories, current activity)
- Integration with scheduler
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from scheduler import get_current_activity, ScheduleBlock


@dataclass
class Personality:
    """Big Five personality traits (0-100 scale)"""
    openness: int          # How receptive to new ideas
    agreeableness: int     # How easily influenced by others
    extraversion: int      # How likely to initiate social contact
    neuroticism: int       # How emotionally reactive
    conscientiousness: int # How organized/disciplined

    def is_extraverted(self) -> bool:
        """Extraverts (>60) initiate more conversations"""
        return self.extraversion > 60

    def is_agreeable(self) -> bool:
        """Agreeable people (>60) are more easily influenced"""
        return self.agreeableness > 60

    def is_open(self) -> bool:
        """Open people (>70) are early adopters of new ideas"""
        return self.openness > 70


@dataclass
class Relationships:
    """Agent's social connections (stored as agent IDs)"""
    relatives: list[str] = field(default_factory=list)
    close_friends: list[str] = field(default_factory=list)
    acquaintances: list[str] = field(default_factory=list)
    colleagues: list[str] = field(default_factory=list)

    def all_connections(self) -> list[str]:
        """All connected agents, ordered by closeness"""
        return self.relatives + self.close_friends + self.acquaintances + self.colleagues

    def get_close_contacts(self) -> list[str]:
        """People this agent would share important news with"""
        return self.relatives + self.close_friends

    def knows(self, agent_id: str) -> bool:
        """Check if this agent knows another agent"""
        return agent_id in self.all_connections()


@dataclass
class Memory:
    """A single memory in the agent's memory stream"""
    id: str
    timestamp: datetime
    content: str                    # What happened
    memory_type: str                # "observation", "conversation", "thought", "reaction"
    related_event_id: str = None    # If this memory is about an injected event
    related_agent_id: str = None    # If this memory involves another agent
    poignancy: int = 5              # 1-10, how important/emotional (affects retrieval)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "memory_type": self.memory_type,
            "related_event_id": self.related_event_id,
            "related_agent_id": self.related_agent_id,
            "poignancy": self.poignancy,
        }


@dataclass
class Agent:
    """
    A single agent in the simulation.

    Static (from JSON):
        id, name, age, occupation, location, avatar, bio
        personality, biases, interests, social_style, relationships, currently

    Dynamic (changes during simulation):
        sentiment, current_thought, known_events, memories
    """
    # === Static Identity ===
    id: str
    name: str
    age: int
    occupation: str
    location: str
    avatar: str
    bio: str
    personality: Personality
    biases: list[str]
    interests: list[str]
    social_style: str
    relationships: Relationships
    currently: str  # Current life situation (can evolve daily)

    # === Dynamic State ===
    sentiment: str = "neutral"              # positive, negative, neutral
    current_thought: str = ""               # Latest thought (shown on click)
    known_events: set[str] = field(default_factory=set)  # Event IDs this agent knows about
    memories: list[Memory] = field(default_factory=list)  # Memory stream

    # === Scheduler Integration ===

    def get_current_activity(self, hour: int) -> ScheduleBlock:
        """What is this agent doing at this hour?"""
        return get_current_activity(self.occupation, hour)

    def can_socialize(self, hour: int) -> bool:
        """Can this agent chat right now?"""
        return self.get_current_activity(hour).can_socialize

    def can_be_interrupted(self, hour: int) -> bool:
        """Can events reach this agent right now?"""
        return self.get_current_activity(hour).can_be_interrupted

    def get_location(self, hour: int) -> str:
        """Where is this agent right now?"""
        return self.get_current_activity(hour).location

    # === Event Knowledge ===

    def knows_about(self, event_id: str) -> bool:
        """Has this agent heard about an event?"""
        return event_id in self.known_events

    def learn_about(self, event_id: str):
        """Mark agent as knowing about an event"""
        self.known_events.add(event_id)

    # === Memory Management ===

    def add_memory(self, content: str, memory_type: str,
                   poignancy: int = 5, related_event_id: str = None,
                   related_agent_id: str = None):
        """Add a new memory to the stream"""
        memory = Memory(
            id=f"mem-{self.id}-{len(self.memories)}",
            timestamp=datetime.now(),
            content=content,
            memory_type=memory_type,
            poignancy=poignancy,
            related_event_id=related_event_id,
            related_agent_id=related_agent_id,
        )
        self.memories.append(memory)
        return memory

    def get_recent_memories(self, limit: int = 10) -> list[Memory]:
        """Get most recent memories"""
        return self.memories[-limit:]

    def get_memories_about_event(self, event_id: str) -> list[Memory]:
        """Get all memories related to a specific event"""
        return [m for m in self.memories if m.related_event_id == event_id]

    def get_memories_about_agent(self, agent_id: str) -> list[Memory]:
        """Get all memories involving another agent"""
        return [m for m in self.memories if m.related_agent_id == agent_id]

    # === Social Behavior ===

    def would_share_news(self) -> bool:
        """Based on personality, would this agent share news with friends?"""
        # Extraverts and high-openness people share more
        return self.personality.is_extraverted() or self.personality.is_open()

    def get_people_to_tell(self) -> list[str]:
        """Who would this agent tell important news to?"""
        if self.personality.extraversion > 80:
            # Very extraverted: tells everyone close
            return self.relationships.get_close_contacts()
        elif self.personality.extraversion > 50:
            # Moderate: tells close friends
            return self.relationships.close_friends[:2]
        else:
            # Introverted: maybe tells one relative
            return self.relationships.relatives[:1]

    # === Serialization ===

    def to_dict(self) -> dict:
        """Convert agent state to dictionary (for frontend/saving)"""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "occupation": self.occupation,
            "location": self.location,
            "avatar": self.avatar,
            "sentiment": self.sentiment,
            "current_thought": self.current_thought,
            "personality": {
                "openness": self.personality.openness,
                "agreeableness": self.personality.agreeableness,
                "extraversion": self.personality.extraversion,
                "neuroticism": self.personality.neuroticism,
                "conscientiousness": self.personality.conscientiousness,
            },
            "biases": self.biases,
            "relationships": {
                "relatives": self.relationships.relatives,
                "close_friends": self.relationships.close_friends,
            },
        }


def load_agents(json_path: str = None) -> dict[str, Agent]:
    """
    Load all agents from JSON file.

    Returns:
        Dictionary mapping agent_id -> Agent object
    """
    if json_path is None:
        json_path = Path(__file__).parent.parent / "data" / "agents.json"

    with open(json_path, "r") as f:
        data = json.load(f)

    agents = {}

    for agent_data in data["agents"]:
        # Parse nested structures
        personality = Personality(**agent_data["personality"])
        relationships = Relationships(**agent_data["relationships"])

        # Create agent
        agent = Agent(
            id=agent_data["id"],
            name=agent_data["name"],
            age=agent_data["age"],
            occupation=agent_data["occupation"],
            location=agent_data["location"],
            avatar=agent_data["avatar"],
            bio=agent_data["bio"],
            personality=personality,
            biases=agent_data["biases"],
            interests=agent_data["interests"],
            social_style=agent_data["social_style"],
            relationships=relationships,
            currently=agent_data["currently"],
        )

        agents[agent.id] = agent

    return agents


# Test when run directly
if __name__ == "__main__":
    agents = load_agents()
    print(f"Loaded {len(agents)} agents\n")

    # Test Elena
    elena = agents["agent-01"]
    print(f"Agent: {elena.name} ({elena.occupation})")
    print(f"  Personality: extraversion={elena.personality.extraversion}")
    print(f"  Is extraverted? {elena.personality.is_extraverted()}")
    print(f"  Would share news? {elena.would_share_news()}")
    print(f"  Would tell: {elena.get_people_to_tell()}")
    print()

    # Test schedule integration
    print("Elena's day:")
    for hour in [7, 10, 13, 20]:
        activity = elena.get_current_activity(hour)
        can_chat = "💬" if elena.can_socialize(hour) else "🔇"
        print(f"  {hour:02d}:00 - {activity.activity} @ {activity.location} {can_chat}")
    print()

    # Test memory
    elena.add_memory(
        content="Had a great morning, café was busy",
        memory_type="observation",
        poignancy=4
    )
    elena.add_memory(
        content="Talked to Liam about the weekend",
        memory_type="conversation",
        poignancy=5,
        related_agent_id="agent-12"
    )
    print(f"Elena's memories ({len(elena.memories)}):")
    for mem in elena.get_recent_memories():
        print(f"  [{mem.memory_type}] {mem.content}")
