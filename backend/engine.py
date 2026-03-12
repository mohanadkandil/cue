"""
Simulation Engine

The main loop that runs the simulation:
- Advances time
- Triggers agent activities
- Processes events and propagation
- Manages state changes
"""

import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from clock import SimulationClock
from agents import Agent, load_agents
from scheduler import get_current_activity
from memory import MemoryStream
from cognition import (
    AgentContext,
    build_personality_summary,
    generate_reaction,
    generate_conversation,
    generate_thought,
)
from spatial import (
    AgentSpatialState,
    LOCATIONS,
    resolve_location,
    initialize_agent_position,
    move_agent_one_step,
    set_agent_target,
    print_agent_positions,
)


@dataclass
class Event:
    """An event injected into the simulation"""
    id: str
    content: str
    created_at: datetime
    source: str = "user"  # "user" or agent_id


@dataclass
class PropagationTask:
    """A pending task for an agent to tell another about an event"""
    from_agent_id: str
    to_agent_id: str
    event_id: str
    summary: str  # What they'll say


@dataclass
class SimulationState:
    """Current state of the simulation"""
    agents: dict[str, Agent]
    memory_streams: dict[str, MemoryStream]
    clock: SimulationClock
    agent_positions: dict[str, AgentSpatialState] = field(default_factory=dict)  # Spatial positions
    events: dict[str, Event] = field(default_factory=dict)
    propagation_queue: list[PropagationTask] = field(default_factory=list)
    feed_items: list[dict] = field(default_factory=list)  # For frontend live feed
    running: bool = False


class SimulationEngine:
    """
    Main simulation engine.

    Runs a loop that:
    1. Advances simulation time
    2. Triggers ambient activity (conversations, thoughts)
    3. Processes injected events
    4. Handles propagation (agents telling others)
    """

    def __init__(
        self,
        tick_interval: float = 1.0,  # Real seconds between ticks
        ambient_conversation_chance: float = 0.1,  # Chance per tick of random convo
        on_state_change: Callable[[dict], None] = None,  # Callback for frontend
        on_feed_update: Callable[[], None] = None,  # Callback for immediate feed updates
    ):
        self.tick_interval = tick_interval
        self.ambient_conversation_chance = ambient_conversation_chance
        self.on_state_change = on_state_change
        self.on_feed_update = on_feed_update  # Called after each feed item added

        # Initialize state
        self.state = self._initialize_state()
        self._event_counter = 0

    def _initialize_state(self) -> SimulationState:
        """Load agents and create initial state"""
        agents = load_agents()

        # Create memory stream for each agent
        memory_streams = {
            agent_id: MemoryStream(agent_id)
            for agent_id in agents.keys()
        }

        # Create clock starting at 6am
        clock = SimulationClock.new(start_hour=6)

        # Initialize spatial positions - distribute across locations
        agent_positions = {}
        location_ids = list(LOCATIONS.keys())
        for i, (agent_id, agent) in enumerate(agents.items()):
            loc_id = location_ids[i % len(location_ids)]
            # Use new tile-event based initialization
            agent_positions[agent_id] = initialize_agent_position(agent_id, loc_id)

        # Debug: print initial positions
        print_agent_positions()

        return SimulationState(
            agents=agents,
            memory_streams=memory_streams,
            clock=clock,
            agent_positions=agent_positions,
        )

    def _get_agent_context(self, agent: Agent, relevant_query: str = None) -> AgentContext:
        """Build AgentContext for LLM calls"""
        # Get relevant memories if query provided
        memories = []
        if relevant_query:
            stream = self.state.memory_streams[agent.id]
            retrieved = stream.retrieve(relevant_query, limit=5)
            memories = [m.content for m in retrieved]

        return AgentContext(
            name=agent.name,
            age=agent.age,
            occupation=agent.occupation,
            bio=agent.bio,
            personality_summary=build_personality_summary({
                "openness": agent.personality.openness,
                "agreeableness": agent.personality.agreeableness,
                "extraversion": agent.personality.extraversion,
                "neuroticism": agent.personality.neuroticism,
                "conscientiousness": agent.personality.conscientiousness,
            }),
            biases=agent.biases,
            current_activity=agent.get_current_activity(self.state.clock.hour).activity,
            current_location=agent.get_current_activity(self.state.clock.hour).location,
            relevant_memories=memories,
        )

    def _add_feed_item(self, content: str, item_type: str = "activity",
                       agent_id: str = None, agent_name: str = None,
                       thought: str = None, sentiment: str = None):
        """Add item to live feed with full context"""
        item = {
            "id": f"feed-{len(self.state.feed_items)}",
            "content": content,
            "type": item_type,
            "timestamp": self.state.clock.current_time.isoformat(),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "thought": thought,
            "sentiment": sentiment,
        }
        self.state.feed_items.insert(0, item)  # Newest first

        # Keep feed limited to last 50 items
        if len(self.state.feed_items) > 50:
            self.state.feed_items = self.state.feed_items[:50]

        # Immediately notify for real-time updates
        if self.on_feed_update:
            self.on_feed_update()

    def _notify_state_change(self):
        """Notify frontend of state changes"""
        if self.on_state_change:
            # Build agent data with positions
            agents_data = {}
            for agent_id, agent in self.state.agents.items():
                agent_dict = agent.to_dict()
                # Add position data from spatial state
                spatial = self.state.agent_positions.get(agent_id)
                if spatial:
                    agent_dict["position"] = spatial.to_dict()
                agents_data[agent_id] = agent_dict

            state_snapshot = {
                "time": self.state.clock.formatted_time,
                "time_of_day": self.state.clock.time_of_day,
                "agents": agents_data,
                "feed": self.state.feed_items[:20],
            }
            self.on_state_change(state_snapshot)

    # =========================================================================
    # Routine Activity (Agents living their day)
    # =========================================================================

    def _process_routine_activities(self):
        """
        Process what agents are doing based on their schedule.
        This makes the world feel alive without events.
        """
        hour = self.state.clock.hour
        minute = self.state.clock.minute

        # Track activity transitions (when schedule block changes)
        for agent in self.state.agents.values():
            current_block = agent.get_current_activity(hour)

            # Store previous activity to detect transitions
            prev_activity = getattr(agent, '_prev_activity', None)
            agent._prev_activity = current_block.activity

            # Activity transition - agent moved to new activity
            if prev_activity and prev_activity != current_block.activity:
                self._handle_activity_transition(agent, prev_activity, current_block)

            # Random chance for agent to have a thought during activity
            if random.random() < 0.05:  # 5% chance per tick
                self._maybe_generate_idle_thought(agent, current_block)

    def _handle_activity_transition(self, agent: Agent, prev_activity: str, new_block):
        """Handle when an agent transitions to a new activity"""
        print(f"[{self.state.clock.formatted_time}] {agent.name}: {prev_activity} → {new_block.activity}")

        self._add_feed_item(
            f"{agent.name} started {new_block.activity} at {new_block.location}",
            item_type="routine"
        )

        # Store transition in memory
        self.state.memory_streams[agent.id].add(
            content=f"Started {new_block.activity} at {new_block.location}",
            memory_type="observation",
            poignancy=2,
        )

    def _maybe_generate_idle_thought(self, agent: Agent, current_block):
        """Maybe generate an idle thought for an agent"""
        if not current_block.can_socialize:
            return  # Don't think during sleep/commute

        ctx = self._get_agent_context(agent)
        situation = f"{current_block.activity} at {current_block.location}"

        thought = generate_thought(ctx, situation)

        if thought and thought != "...":
            agent.current_thought = thought
            print(f"[{self.state.clock.formatted_time}] {agent.name} thinks: {thought[:60]}...")

    # =========================================================================
    # Movement Processing
    # =========================================================================

    def _process_movement(self):
        """
        Movement using generative_agents style:
        - Agents tracked as events on tiles
        - BFS pathfinding
        - Move 1 tile per tick
        - Collision avoidance by checking tile events
        """
        hour = self.state.clock.hour

        for agent_id, agent in self.state.agents.items():
            spatial = self.state.agent_positions.get(agent_id)
            if not spatial:
                continue

            # Get scheduled location
            scheduled = agent.get_current_activity(hour)
            target_loc = resolve_location(scheduled.location)
            if not target_loc:
                continue

            # Set new target if location changed
            if spatial.location_id != target_loc:
                if set_agent_target(spatial, target_loc):
                    print(f"[{self.state.clock.formatted_time}] {agent.name} → {target_loc}")

            # Move one step along path
            move_agent_one_step(spatial)

    # =========================================================================
    # Ambient Activity (Conversations)
    # =========================================================================

    def _maybe_trigger_ambient_conversation(self):
        """Maybe trigger a random conversation between two agents"""
        if random.random() > self.ambient_conversation_chance:
            return

        hour = self.state.clock.hour

        # Find agents who can socialize
        available = [
            agent for agent in self.state.agents.values()
            if agent.can_socialize(hour)
        ]

        if len(available) < 2:
            return

        # Pick two connected agents
        agent1 = random.choice(available)
        connections = agent1.relationships.all_connections()
        available_connections = [
            self.state.agents[aid]
            for aid in connections
            if aid in self.state.agents and self.state.agents[aid].can_socialize(hour)
        ]

        if not available_connections:
            return

        agent2 = random.choice(available_connections)

        # Generate conversation
        ctx1 = self._get_agent_context(agent1)
        ctx2 = self._get_agent_context(agent2)

        print(f"[{self.state.clock.formatted_time}] Ambient: {agent1.name} chats with {agent2.name}")

        result = generate_conversation(ctx1, ctx2)

        # Store in memories
        topic = result.get("topic", "casual conversation")
        self.state.memory_streams[agent1.id].add(
            content=f"Had a {result.get('mood', 'casual')} conversation with {agent2.name} about {topic}",
            memory_type="conversation",
            poignancy=4,
            related_agent_id=agent2.id,
        )
        self.state.memory_streams[agent2.id].add(
            content=f"Had a {result.get('mood', 'casual')} conversation with {agent1.name} about {topic}",
            memory_type="conversation",
            poignancy=4,
            related_agent_id=agent1.id,
        )

        # Add to feed with context
        self._add_feed_item(
            f"{agent1.name} chatted with {agent2.name}",
            item_type="conversation",
            agent_id=agent1.id,
            agent_name=agent1.name,
            thought=f"Topic: {topic}. Mood: {result.get('mood', 'casual')}",
        )

    # =========================================================================
    # Event Processing
    # =========================================================================

    def inject_event(self, content: str, source: str = "user") -> Event:
        """
        Inject an event into the simulation.

        This triggers:
        1. Early adopters perceive and react
        2. Some decide to share with friends (propagation)
        """
        self._event_counter += 1
        event = Event(
            id=f"event-{self._event_counter}",
            content=content,
            created_at=datetime.now(),
            source=source,
        )
        self.state.events[event.id] = event

        print(f"\n{'='*50}")
        print(f"EVENT INJECTED: {content}")
        print(f"{'='*50}\n")

        self._add_feed_item(f"📢 {content}", item_type="event")

        # Find early perceivers - agents who can receive news now
        hour = self.state.clock.hour
        available = [
            agent for agent in self.state.agents.values()
            if agent.can_be_interrupted(hour)
        ]

        # Prioritize high openness agents, but always pick some
        high_openness = [a for a in available if a.personality.openness > 50]
        if high_openness:
            perceivers = random.sample(high_openness, min(5, len(high_openness)))
        else:
            perceivers = random.sample(available, min(5, len(available))) if available else []

        print(f"Early perceivers: {[a.name for a in perceivers]}")

        # Process reactions with small delays for real-time updates
        for agent in perceivers:
            self._process_agent_reaction(agent, event)
            time.sleep(0.1)  # Small delay to allow broadcast to go through

        return event

    def _process_agent_reaction(self, agent: Agent, event: Event):
        """Process an agent's reaction to an event"""
        if agent.knows_about(event.id):
            return  # Already knows

        agent.learn_about(event.id)

        # Get context with relevant memories
        ctx = self._get_agent_context(agent, relevant_query=event.content)

        print(f"  {agent.name} reacting...")

        # Generate reaction
        reaction = generate_reaction(ctx, event.content)

        # Update agent state
        agent.sentiment = reaction["sentiment"]
        agent.current_thought = reaction["thought"]

        # Store in memory
        self.state.memory_streams[agent.id].add(
            content=f"Heard about: {event.content}. Felt {reaction['sentiment']}. Thought: {reaction['thought']}",
            memory_type="reaction",
            poignancy=7,
            related_event_id=event.id,
        )

        # Add to feed with full context
        sentiment_emoji = {"positive": "😊", "negative": "😠", "neutral": "😐"}.get(reaction["sentiment"], "")
        self._add_feed_item(
            f"{agent.name} {sentiment_emoji} reacted to the news",
            item_type="reaction",
            agent_id=agent.id,
            agent_name=agent.name,
            thought=reaction["thought"],
            sentiment=reaction["sentiment"],
        )

        print(f"    Sentiment: {reaction['sentiment']}")
        print(f"    Thought: {reaction['thought'][:80]}...")

        # Maybe propagate to friends
        if reaction["would_share"]:
            contacts = agent.get_people_to_tell()
            for contact_id in contacts:
                if contact_id in self.state.agents:
                    self.state.propagation_queue.append(PropagationTask(
                        from_agent_id=agent.id,
                        to_agent_id=contact_id,
                        event_id=event.id,
                        summary=reaction["share_summary"],
                    ))
            print(f"    Will tell: {contacts}")

    def _process_propagation_queue(self):
        """Process pending propagation tasks"""
        if not self.state.propagation_queue:
            return

        # Process a few propagations per tick (not all at once)
        tasks_to_process = self.state.propagation_queue[:3]
        self.state.propagation_queue = self.state.propagation_queue[3:]

        for task in tasks_to_process:
            from_agent = self.state.agents[task.from_agent_id]
            to_agent = self.state.agents[task.to_agent_id]
            event = self.state.events[task.event_id]

            # Check if receiver can be interrupted
            if not to_agent.can_be_interrupted(self.state.clock.hour):
                # Re-queue for later
                self.state.propagation_queue.append(task)
                continue

            # Skip if already knows
            if to_agent.knows_about(event.id):
                continue

            print(f"[{self.state.clock.formatted_time}] {from_agent.name} tells {to_agent.name} about event")

            # Add to feed
            self._add_feed_item(
                f"{from_agent.name} told {to_agent.name} about the news",
                item_type="propagation",
                agent_id=from_agent.id,
                agent_name=from_agent.name,
                thought=task.summary,
            )

            # Process their reaction
            self._process_agent_reaction(to_agent, event)

    # =========================================================================
    # Main Loop
    # =========================================================================

    def tick(self):
        """Process one simulation tick"""
        # Advance time
        self.state.clock.tick()

        # Process agent movement (update positions, trigger walks)
        self._process_movement()

        # Process routine activities (agents living their day)
        self._process_routine_activities()

        # Maybe trigger ambient conversation
        self._maybe_trigger_ambient_conversation()

        # Process propagation queue
        self._process_propagation_queue()

        # Notify frontend
        self._notify_state_change()

    def run(self, duration_seconds: float = None):
        """
        Run the simulation loop.

        Args:
            duration_seconds: How long to run (None = forever)
        """
        self.state.running = True
        start_time = time.time()

        print(f"Simulation started at {self.state.clock.formatted_datetime}")
        print(f"Tick interval: {self.tick_interval}s (each tick = {self.state.clock.tick_duration} sim minutes)")
        print("-" * 50)

        try:
            while self.state.running:
                self.tick()

                # Check duration
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    break

                time.sleep(self.tick_interval)

        except KeyboardInterrupt:
            print("\nSimulation stopped by user")

        self.state.running = False
        print(f"\nSimulation ended at {self.state.clock.formatted_datetime}")

    def stop(self):
        """Stop the simulation"""
        self.state.running = False


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("Simulation Engine Test\n")
    print("=" * 50)

    # Create engine
    engine = SimulationEngine(
        tick_interval=0.5,  # Fast for testing
        ambient_conversation_chance=0.2,  # 20% chance per tick
    )

    print(f"Loaded {len(engine.state.agents)} agents")
    print(f"Starting time: {engine.state.clock.formatted_datetime}")
    print(f"Each tick = {engine.state.clock.tick_duration} simulation minutes")
    print()

    # Run simulation for a simulated hour (12 ticks at 5 min each)
    print("=" * 50)
    print("PHASE 1: Morning routine (no events)")
    print("=" * 50)

    for i in range(12):  # 1 hour of sim time
        print(f"\n--- {engine.state.clock.formatted_time} ---")
        engine.tick()
        time.sleep(0.5)

    print("\n")
    print("=" * 50)
    print("PHASE 2: Injecting event")
    print("=" * 50)

    engine.inject_event("NovaCRM announces a 40% price increase effective next month")

    # Run more ticks to see propagation
    print("\n")
    print("=" * 50)
    print("PHASE 3: Watching propagation")
    print("=" * 50)

    for i in range(10):
        print(f"\n--- {engine.state.clock.formatted_time} ---")
        engine.tick()
        time.sleep(0.5)

    # Show final state
    print("\n" + "=" * 50)
    print("FINAL STATE")
    print("=" * 50)

    print(f"\nSimulation time: {engine.state.clock.formatted_datetime}")

    print("\nAgent sentiments after event:")
    sentiments = {"positive": [], "negative": [], "neutral": []}
    for agent in engine.state.agents.values():
        sentiments[agent.sentiment].append(agent.name)

    print(f"  Positive ({len(sentiments['positive'])}): {', '.join(sentiments['positive'][:5])}...")
    print(f"  Negative ({len(sentiments['negative'])}): {', '.join(sentiments['negative'][:5])}...")
    print(f"  Neutral ({len(sentiments['neutral'])}): {len(sentiments['neutral'])} agents")

    print(f"\nPropagation queue remaining: {len(engine.state.propagation_queue)}")

    print("\nRecent feed items:")
    for item in engine.state.feed_items[:15]:
        print(f"  [{item['type']:12}] {item['content']}")
