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
    generate_reflection,
    generate_daily_plan,
    decompose_task,
)
from spatial import (
    AgentSpatialState,
    LOCATIONS,
    resolve_location,
    initialize_agent_position,
    move_agent_one_step,
    set_agent_target,
    print_agent_positions,
    get_nearby_agents,
    get_agents_at_same_location,
    perceive_surroundings,
    get_proximity_pairs,
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
class ScheduleBlock:
    """A single block in an agent's daily schedule"""
    hour: int
    duration: int
    activity: str
    location: str
    can_be_interrupted: bool
    subtasks: list[dict] = field(default_factory=list)  # Decomposed tasks


@dataclass
class DailyPlan:
    """An agent's plan for the day (LLM-generated)"""
    agent_id: str
    day: int  # Simulation day number
    wake_up_hour: int
    sleep_hour: int
    schedule: list[ScheduleBlock] = field(default_factory=list)

    def get_activity_at(self, hour: int) -> ScheduleBlock | None:
        """Get what the agent is doing at a specific hour"""
        for block in self.schedule:
            if block.hour <= hour < block.hour + block.duration:
                return block
        return None


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
    # Track last reflection time for each agent (for periodic reflection)
    last_reflection: dict[str, datetime] = field(default_factory=dict)
    # Dynamic daily plans for each agent (LLM-generated)
    daily_plans: dict[str, DailyPlan] = field(default_factory=dict)
    # Track which sim day we're on (for knowing when to regenerate plans)
    current_day: int = 1


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
        """Maybe trigger a conversation between two NEARBY agents"""
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

        # Pick an agent and find nearby agents (spatial awareness!)
        agent1 = random.choice(available)

        # Get agents at same location (can actually talk)
        nearby_ids = get_agents_at_same_location(agent1.id, self.state.agent_positions)

        # Filter to those who can socialize
        nearby_available = [
            self.state.agents[aid]
            for aid in nearby_ids
            if aid in self.state.agents and self.state.agents[aid].can_socialize(hour)
        ]

        if not nearby_available:
            return

        agent2 = random.choice(nearby_available)

        # Get recent important memories for both agents (natural context)
        recent1 = self.state.memory_streams[agent1.id].get_recent(limit=3)
        recent2 = self.state.memory_streams[agent2.id].get_recent(limit=3)

        # Build context with recent memories so LLM knows what's on their mind
        ctx1 = self._get_agent_context(agent1)
        ctx1.relevant_memories = [m.content for m in recent1 if m.poignancy >= 5]

        ctx2 = self._get_agent_context(agent2)
        ctx2.relevant_memories = [m.content for m in recent2 if m.poignancy >= 5]

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

        # Add to feed - show actual conversation snippet
        exchanges = result.get("exchanges", [])
        if exchanges:
            snippet = exchanges[0].get("message", "")[:100]
            self._add_feed_item(
                f"{agent1.name} to {agent2.name}: \"{snippet}\"",
                item_type="conversation",
                agent_id=agent1.id,
                agent_name=agent1.name,
                thought=f"Topic: {topic}",
            )
        else:
            self._add_feed_item(
                f"{agent1.name} chatted with {agent2.name} about {topic}",
                item_type="conversation",
                agent_id=agent1.id,
                agent_name=agent1.name,
            )

    # =========================================================================
    # Perception - Agents see nearby agents
    # =========================================================================

    def _process_perception(self):
        """
        Agents perceive who's nearby and create observation memories.

        This runs occasionally (not every tick) to avoid too many memories.
        Agents notice who's around them and what they're doing.
        """
        # Get current activities for all agents
        agent_activities = {}
        for agent_id, agent in self.state.agents.items():
            activity = self.get_agent_current_activity(agent_id)
            agent_activities[agent_id] = activity

        # Each agent perceives surroundings
        for agent_id, agent in self.state.agents.items():
            perceptions = perceive_surroundings(
                agent_id,
                self.state.agent_positions,
                agent_activities,
            )

            # Create observation memories for nearby agents
            for perception in perceptions[:3]:  # Limit to 3 closest
                if perception["type"] == "agent":
                    other_id = perception["agent_id"]
                    other_agent = self.state.agents.get(other_id)

                    if other_agent:
                        activity = perception.get("activity", "around")
                        distance = perception.get("distance", 0)

                        # Only notice if close enough
                        if distance <= 3:
                            memory_content = f"Noticed {other_agent.name} {activity} nearby"

                            # Check if we already have a recent similar memory
                            recent = self.state.memory_streams[agent_id].get_recent(5)
                            already_noticed = any(
                                other_agent.name in m.content and "Noticed" in m.content
                                for m in recent
                            )

                            if not already_noticed:
                                self.state.memory_streams[agent_id].add(
                                    content=memory_content,
                                    memory_type="observation",
                                    poignancy=2,
                                    related_agent_id=other_id,
                                )

    # =========================================================================
    # Reflection
    # =========================================================================

    def _maybe_trigger_reflection(self):
        """
        Periodically trigger reflection for agents.

        Reflection happens when:
        - Agent has accumulated enough memories (>= 10 since last reflection)
        - OR enough time has passed (e.g., every simulated hour)

        This is what makes agents "understand" their experiences over time.
        """
        now = datetime.now()

        for agent_id, agent in self.state.agents.items():
            stream = self.state.memory_streams[agent_id]

            # Check if agent has enough memories to reflect
            if stream.count() < 5:
                continue

            # Check cooldown (don't reflect too often - once per sim hour max)
            last = self.state.last_reflection.get(agent_id)
            if last:
                # In real sim, check sim time. For now, use real time with short cooldown
                if (now - last).total_seconds() < 60:  # 1 minute real time cooldown
                    continue

            # Get recent memories for reflection
            recent = stream.get_recent(limit=10)
            recent_texts = [m.content for m in recent]

            # Build context
            ctx = self._get_agent_context(agent)

            # Generate insights
            insights = generate_reflection(ctx, recent_texts)

            if insights:
                print(f"[{self.state.clock.formatted_time}] {agent.name} reflects...")

                for insight_data in insights:
                    insight_text = insight_data.get("insight", "")
                    importance = insight_data.get("importance", 5)

                    if insight_text:
                        # Store insight as a high-importance memory
                        stream.add(
                            content=f"[Reflection] {insight_text}",
                            memory_type="reflection",
                            poignancy=min(importance + 2, 10),  # Reflections are important
                        )

                        # Add to feed
                        self._add_feed_item(
                            f"{agent.name} realized: \"{insight_text}\"",
                            item_type="reflection",
                            agent_id=agent.id,
                            agent_name=agent.name,
                            thought=insight_text,
                        )

                        print(f"  → \"{insight_text}\" (importance: {importance})")

            # Update last reflection time
            self.state.last_reflection[agent_id] = now

    # =========================================================================
    # Dynamic Planning
    # =========================================================================

    def _generate_daily_plan_for_agent(self, agent: Agent) -> DailyPlan:
        """
        Generate a personalized daily plan for one agent.

        This creates a unique schedule based on their personality,
        occupation, and recent experiences - unlike static schedules.
        """
        ctx = self._get_agent_context(agent)

        # Get yesterday's summary from memories
        stream = self.state.memory_streams[agent.id]
        recent = stream.get_recent(limit=5)
        yesterday_summary = "; ".join([m.content for m in recent]) if recent else None

        # Generate plan via LLM
        plan_data = generate_daily_plan(ctx, yesterday_summary)

        # Convert to ScheduleBlocks
        schedule = []
        for block_data in plan_data.get("schedule", []):
            block = ScheduleBlock(
                hour=block_data["hour"],
                duration=block_data["duration"],
                activity=block_data["activity"],
                location=block_data["location"],
                can_be_interrupted=block_data["can_be_interrupted"],
            )
            schedule.append(block)

        return DailyPlan(
            agent_id=agent.id,
            day=self.state.current_day,
            wake_up_hour=plan_data.get("wake_up_hour", 7),
            sleep_hour=plan_data.get("sleep_hour", 22),
            schedule=schedule,
        )

    def _maybe_generate_daily_plans(self):
        """
        Generate daily plans for all agents at the start of a new day.

        Called when simulation hour is 6 (morning) and plans are outdated.
        """
        hour = self.state.clock.hour

        # Only generate plans in the early morning
        if hour != 6:
            return

        # Check if we already have plans for today
        sample_plan = next(iter(self.state.daily_plans.values()), None) if self.state.daily_plans else None
        if sample_plan and sample_plan.day == self.state.current_day:
            return  # Already have today's plans

        print(f"\n[{self.state.clock.formatted_time}] === GENERATING DAILY PLANS ===")

        for agent_id, agent in self.state.agents.items():
            print(f"  Planning {agent.name}'s day...")
            plan = self._generate_daily_plan_for_agent(agent)
            self.state.daily_plans[agent_id] = plan

            # Log their schedule
            for block in plan.schedule[:3]:  # Show first 3 activities
                print(f"    {block.hour:02d}:00 - {block.activity} @ {block.location}")
            if len(plan.schedule) > 3:
                print(f"    ... and {len(plan.schedule) - 3} more activities")

            # Add to feed
            self._add_feed_item(
                f"{agent.name} planned their day",
                item_type="planning",
                agent_id=agent.id,
                agent_name=agent.name,
                thought=f"First activity: {plan.schedule[0].activity}" if plan.schedule else "Resting",
            )

        print(f"[{self.state.clock.formatted_time}] === PLANS COMPLETE ===\n")

    def get_agent_current_activity(self, agent_id: str) -> str:
        """
        Get what an agent is currently doing based on their dynamic plan.

        Falls back to static schedule if no plan exists.
        """
        plan = self.state.daily_plans.get(agent_id)
        if plan:
            block = plan.get_activity_at(self.state.clock.hour)
            if block:
                return block.activity

        # Fallback to static schedule
        agent = self.state.agents[agent_id]
        return agent.get_current_activity(self.state.clock.hour).activity

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

        # 6 agents react immediately
        high_openness = [a for a in available if a.personality.openness > 50]
        if high_openness:
            perceivers = random.sample(high_openness, min(6, len(high_openness)))
        else:
            perceivers = random.sample(available, min(6, len(available))) if available else []

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

        # Add to feed - show what they actually said (skip empty thoughts)
        thought = reaction.get("thought", "").strip()
        if thought and thought != "..." and len(thought) > 10:
            self._add_feed_item(
                f"{agent.name}: \"{thought}\"",
                item_type="reaction",
                agent_id=agent.id,
                agent_name=agent.name,
                thought=thought,
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

        # Generate daily plans at start of each day (6am)
        # Disabled for now - too slow, blocks real-time updates
        # self._maybe_generate_daily_plans()

        # Process agent movement (update positions, trigger walks)
        self._process_movement()

        # Agents perceive who's nearby (creates observation memories)
        if random.random() < 0.15:  # 15% chance per tick
            self._process_perception()

        # Process routine activities (agents living their day)
        self._process_routine_activities()

        # Maybe trigger ambient conversation (now uses spatial awareness)
        self._maybe_trigger_ambient_conversation()

        # Maybe trigger reflection (agents forming insights)
        if random.random() < 0.1:  # 10% chance per tick
            self._maybe_trigger_reflection()

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
