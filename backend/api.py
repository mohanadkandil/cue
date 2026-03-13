"""
API Server - Simplified

Provides:
- WebSocket for real-time updates to frontend
- REST endpoints for event injection and state queries
"""

import asyncio
import json
import sys
from typing import Set, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Delay heavy imports
engine = None
simulation_task = None


def _create_engine():
    """Create engine (called in thread)"""
    from engine import SimulationEngine
    print("Creating simulation engine...", file=sys.stderr, flush=True)
    eng = SimulationEngine(
        tick_interval=1.0,
        ambient_conversation_chance=0.15,
    )
    print(f"Loaded {len(eng.state.agents)} agents", file=sys.stderr, flush=True)
    return eng


# Queue for feed updates that need broadcasting
feed_update_queue = []


def on_feed_update_callback():
    """Called by engine when feed is updated"""
    feed_update_queue.append(True)


async def get_engine_async():
    """Lazy load engine on first use (async)"""
    global engine
    if engine is None:
        loop = asyncio.get_event_loop()
        engine = await loop.run_in_executor(None, _create_engine)
    return engine


def get_engine():
    """Lazy load engine on first use (sync)"""
    global engine
    if engine is None:
        engine = _create_engine()
    return engine


# =============================================================================
# WebSocket Manager
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        if not self.active_connections:
            return

        print(f"[BROADCAST] Sending to {len(self.active_connections)} clients", file=sys.stderr, flush=True)
        data = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.active_connections.discard(conn)


manager = ConnectionManager()


# =============================================================================
# Simulation Runner
# =============================================================================

async def run_simulation():
    """Run simulation loop asynchronously"""
    global engine
    eng = engine
    if not eng:
        print("ERROR: Engine not initialized!", file=sys.stderr)
        return
    print("Simulation loop started", file=sys.stderr, flush=True)

    loop = asyncio.get_event_loop()
    while True:
        try:
            # Run tick in thread pool to avoid blocking
            await loop.run_in_executor(None, eng.tick)

            # Broadcast state to all clients
            state = get_state_snapshot()
            await manager.broadcast({
                "type": "state_update",
                "data": state
            })

            await asyncio.sleep(eng.tick_interval)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Simulation error: {e}", file=sys.stderr)
            await asyncio.sleep(1)


def get_state_snapshot() -> dict:
    """Get current simulation state for frontend"""
    from spatial import get_proximity_pairs

    global engine
    eng = engine
    if not eng:
        return {"time": "", "datetime": "", "agents": [], "feed": [], "proximity": [], "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0}}
    agents_data = []
    for agent in eng.state.agents.values():
        agent_data = {
            "id": agent.id,
            "name": agent.name,
            "avatar": agent.avatar,
            "occupation": agent.occupation,
            "sentiment": agent.sentiment,
            "current_thought": agent.current_thought,
            "location": agent.get_location(eng.state.clock.hour),
            "activity": agent.get_current_activity(eng.state.clock.hour).activity,
            "can_socialize": agent.can_socialize(eng.state.clock.hour),
            "personality": {
                "openness": agent.personality.openness,
                "agreeableness": agent.personality.agreeableness,
                "extraversion": agent.personality.extraversion,
            },
            "friends": agent.relationships.all_connections(),
        }
        spatial = eng.state.agent_positions.get(agent.id)
        if spatial:
            agent_data["position"] = spatial.to_dict()
        agents_data.append(agent_data)

    proximity_pairs = get_proximity_pairs(eng.state.agent_positions, max_distance=4)
    proximity_data = [
        {"source": a1, "target": a2, "distance": round(d, 1)}
        for a1, a2, d in proximity_pairs
    ]

    return {
        "time": eng.state.clock.formatted_time,
        "datetime": eng.state.clock.formatted_datetime,
        "time_of_day": eng.state.clock.time_of_day,
        "agents": agents_data,
        "feed": eng.state.feed_items[:30],
        "sentiment_counts": {
            "positive": sum(1 for a in eng.state.agents.values() if a.sentiment == "positive"),
            "negative": sum(1 for a in eng.state.agents.values() if a.sentiment == "negative"),
            "neutral": sum(1 for a in eng.state.agents.values() if a.sentiment == "neutral"),
        },
        "propagation_pending": len(eng.state.propagation_queue),
        "proximity": proximity_data,
    }


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Cue Simulation API",
    description="Real-time AI agent simulation",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# REST Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Health check - doesn't require engine"""
    global engine
    if engine:
        return {"status": "running", "time": engine.state.clock.formatted_time}
    return {"status": "starting", "time": "initializing..."}


@app.get("/state")
async def get_state():
    """Get current simulation state"""
    await get_engine_async()  # Ensure engine is loaded
    return get_state_snapshot()


@app.get("/agents")
async def get_agents():
    """Get all agents"""
    eng = get_engine()
    return {
        "agents": [agent.to_dict() for agent in eng.state.agents.values()]
    }


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    eng = get_engine()
    agent = eng.state.agents.get(agent_id)
    if not agent:
        return {"error": "Agent not found"}

    memories = eng.state.memory_streams[agent_id].get_recent(limit=10)

    return {
        "agent": agent.to_dict(),
        "memories": [
            {
                "content": m.content,
                "type": m.memory_type,
                "timestamp": m.created_at.isoformat(),
            }
            for m in memories
        ],
        "current_activity": agent.get_current_activity(eng.state.clock.hour).activity,
        "location": agent.get_location(eng.state.clock.hour),
    }


@app.post("/inject")
async def inject_event_endpoint(event: dict):
    """Inject an event into the simulation"""
    content = event.get("content")
    if not content:
        return {"error": "Missing 'content' field"}

    eng = get_engine()
    loop = asyncio.get_event_loop()
    injected = await loop.run_in_executor(None, eng.inject_event, content)

    # Broadcast immediately so frontend sees the update
    state = get_state_snapshot()
    await manager.broadcast({
        "type": "state_update",
        "data": state
    })

    return {
        "success": True,
        "event_id": injected.id,
        "content": injected.content,
    }


@app.get("/feed")
async def get_feed():
    """Get live feed items"""
    eng = get_engine()
    return {"feed": eng.state.feed_items[:50]}


@app.post("/poll")
async def poll_all_agents(event: dict):
    """
    Quick poll of ALL agents for instant feedback.

    Returns aggregate sentiment stats, key insight, and notable responses.
    This is the "Phase 1" quick feedback before opening the sandbox.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from cognition import (
        AgentContext,
        build_personality_summary,
        generate_poll_reaction,
        generate_poll_summary,
    )
    import time

    content = event.get("content")
    if not content:
        return {"error": "Missing 'content' field"}

    start_time = time.time()

    eng = await get_engine_async()

    # Prepare contexts for all agents
    agents_list = list(eng.state.agents.values())

    def get_agent_reaction(agent):
        """Get reaction from a single agent"""
        ctx = AgentContext(
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
            current_activity=agent.get_current_activity(eng.state.clock.hour).activity,
            current_location=agent.get_current_activity(eng.state.clock.hour).location,
            relevant_memories=[],  # Skip for speed
        )

        reaction = generate_poll_reaction(ctx, content)

        return {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "occupation": agent.occupation,
            "avatar": agent.avatar,
            "thought": reaction["thought"],
            "sentiment": reaction["sentiment"],
            "intensity": reaction.get("intensity", 3),
        }

    # Poll all agents in parallel using thread pool
    reactions = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_agent_reaction, agent): agent for agent in agents_list}

        for future in as_completed(futures):
            try:
                result = future.result(timeout=30)
                reactions.append(result)
            except Exception as e:
                print(f"Agent reaction failed: {e}", file=sys.stderr)

    # Aggregate sentiment counts
    sentiment_counts = {"positive": 0, "curious": 0, "skeptical": 0, "negative": 0}
    for r in reactions:
        sentiment = r["sentiment"]
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1

    # Calculate percentages
    total = len(reactions)
    sentiment_percentages = {
        k: round(v / total * 100) if total > 0 else 0
        for k, v in sentiment_counts.items()
    }

    # Generate summary insight
    summary = generate_poll_summary(content, reactions, sentiment_counts)

    # Find notable responses (high intensity, interesting mix)
    notable = []
    # Get 1-2 positive with high intensity
    positive_reactions = [r for r in reactions if r["sentiment"] == "positive"]
    positive_reactions.sort(key=lambda x: x.get("intensity", 3), reverse=True)
    notable.extend(positive_reactions[:2])

    # Get 1 negative/skeptical with high intensity
    critical_reactions = [r for r in reactions if r["sentiment"] in ("negative", "skeptical")]
    critical_reactions.sort(key=lambda x: x.get("intensity", 3), reverse=True)
    notable.extend(critical_reactions[:1])

    # Format notable for frontend
    notable_formatted = [
        {
            "name": r["agent_name"],
            "role": r["occupation"],
            "text": r["thought"],
            "sentiment": "positive" if r["sentiment"] in ("positive", "curious") else "negative",
            "avatar": r.get("avatar", ""),
        }
        for r in notable
    ]

    elapsed = time.time() - start_time

    return {
        "success": True,
        "event": content,
        "agent_count": total,
        "elapsed_seconds": round(elapsed, 1),
        "sentiment_percentages": sentiment_percentages,
        "sentiment_counts": sentiment_counts,
        "key_insight": summary.get("key_insight", ""),
        "notable_themes": summary.get("notable_themes", []),
        "notable_responses": notable_formatted,
        "all_reactions": reactions,  # Full data for detailed view
    }


@app.get("/events")
async def sse_events():
    """Server-Sent Events endpoint for real-time updates"""
    async def generate():
        # Ensure engine is loaded
        await get_engine_async()

        # Start simulation if not running
        global simulation_task
        if simulation_task is None or simulation_task.done():
            simulation_task = asyncio.create_task(run_simulation_background())

        last_feed_len = 0
        while True:
            try:
                state = get_state_snapshot()
                # Always send update (frontend will dedupe)
                data = json.dumps(state)
                yield f"data: {data}\n\n"
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"SSE error: {e}", file=sys.stderr)
                await asyncio.sleep(1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


async def run_simulation_background():
    """Run simulation loop in background"""
    global engine
    eng = engine
    if not eng:
        print("ERROR: Engine not initialized!", file=sys.stderr)
        return
    print("Simulation background loop started", file=sys.stderr, flush=True)

    loop = asyncio.get_event_loop()
    while True:
        try:
            await loop.run_in_executor(None, eng.tick)
            await asyncio.sleep(eng.tick_interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Simulation error: {e}", file=sys.stderr)
            await asyncio.sleep(1)


# =============================================================================
# WebSocket
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    global simulation_task

    await manager.connect(websocket)

    # Initialize engine and start simulation if not running
    await get_engine_async()
    if simulation_task is None or simulation_task.done():
        simulation_task = asyncio.create_task(run_simulation())

    # Send initial state
    try:
        await websocket.send_json({
            "type": "initial_state",
            "data": get_state_snapshot()
        })
    except Exception as e:
        print(f"Error sending initial state: {e}", file=sys.stderr)

    # Keep connection alive
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "inject":
                content = message.get("content")
                if content:
                    eng = get_engine()
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, eng.inject_event, content)

            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}", file=sys.stderr)
        manager.disconnect(websocket)


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
