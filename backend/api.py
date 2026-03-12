"""
API Server

Provides:
- WebSocket for real-time updates to frontend
- REST endpoints for event injection and state queries
"""

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from engine import SimulationEngine


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
        print(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        if not self.active_connections:
            return

        data = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)


manager = ConnectionManager()
engine: SimulationEngine = None
simulation_task: asyncio.Task = None
broadcast_queue: asyncio.Queue = None
broadcast_task: asyncio.Task = None


# =============================================================================
# Simulation Runner
# =============================================================================

async def broadcast_worker():
    """Worker that processes broadcast queue for real-time updates"""
    global broadcast_queue
    while True:
        try:
            await broadcast_queue.get()
            state = get_state_snapshot()
            await manager.broadcast({
                "type": "state_update",
                "data": state
            })
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Broadcast error: {e}")


def trigger_broadcast():
    """Called by engine when feed updates - schedules immediate broadcast"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(do_broadcast(), loop)
    except:
        pass


async def do_broadcast():
    """Actually send the broadcast"""
    state = get_state_snapshot()
    await manager.broadcast({
        "type": "state_update",
        "data": state
    })


async def run_simulation():
    """Run simulation loop asynchronously"""
    print("Simulation loop started")

    while True:
        try:
            # Run one tick
            engine.tick()

            # Broadcast state to all clients
            state = get_state_snapshot()
            await manager.broadcast({
                "type": "state_update",
                "data": state
            })

            # Wait before next tick
            await asyncio.sleep(engine.tick_interval)

        except asyncio.CancelledError:
            print("Simulation loop cancelled")
            break
        except Exception as e:
            print(f"Simulation error: {e}")
            await asyncio.sleep(1)


def get_state_snapshot() -> dict:
    """Get current simulation state for frontend"""
    agents_data = []
    for agent in engine.state.agents.values():
        agent_data = {
            "id": agent.id,
            "name": agent.name,
            "avatar": agent.avatar,
            "occupation": agent.occupation,
            "sentiment": agent.sentiment,
            "current_thought": agent.current_thought,
            "location": agent.get_location(engine.state.clock.hour),
            "activity": agent.get_current_activity(engine.state.clock.hour).activity,
            "can_socialize": agent.can_socialize(engine.state.clock.hour),
            "personality": {
                "openness": agent.personality.openness,
                "agreeableness": agent.personality.agreeableness,
                "extraversion": agent.personality.extraversion,
            },
            "friends": agent.relationships.all_connections(),
        }
        # Add position data from spatial state
        spatial = engine.state.agent_positions.get(agent.id)
        if spatial:
            agent_data["position"] = spatial.to_dict()
        agents_data.append(agent_data)

    return {
        "time": engine.state.clock.formatted_time,
        "datetime": engine.state.clock.formatted_datetime,
        "time_of_day": engine.state.clock.time_of_day,
        "agents": agents_data,
        "feed": engine.state.feed_items[:30],
        "sentiment_counts": {
            "positive": sum(1 for a in engine.state.agents.values() if a.sentiment == "positive"),
            "negative": sum(1 for a in engine.state.agents.values() if a.sentiment == "negative"),
            "neutral": sum(1 for a in engine.state.agents.values() if a.sentiment == "neutral"),
        },
        "propagation_pending": len(engine.state.propagation_queue),
    }


# =============================================================================
# FastAPI App
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global engine, simulation_task, broadcast_queue, broadcast_task

    # Startup
    print("Starting simulation engine...")

    # Create broadcast queue for real-time updates
    broadcast_queue = asyncio.Queue(maxsize=100)

    engine = SimulationEngine(
        tick_interval=1.0,  # 1 second between ticks
        ambient_conversation_chance=0.15,
        on_feed_update=trigger_broadcast,  # Real-time feed updates
    )
    print(f"Loaded {len(engine.state.agents)} agents")

    # Start broadcast worker
    broadcast_task = asyncio.create_task(broadcast_worker())

    # Start simulation loop
    simulation_task = asyncio.create_task(run_simulation())

    yield

    # Shutdown
    print("Shutting down...")
    if broadcast_task:
        broadcast_task.cancel()
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass
    if simulation_task:
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Cue Simulation API",
    description="Real-time AI agent simulation",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# REST Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Health check"""
    return {"status": "running", "time": engine.state.clock.formatted_time if engine else "not started"}


@app.get("/state")
async def get_state():
    """Get current simulation state"""
    return get_state_snapshot()


@app.get("/agents")
async def get_agents():
    """Get all agents"""
    return {
        "agents": [agent.to_dict() for agent in engine.state.agents.values()]
    }


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    agent = engine.state.agents.get(agent_id)
    if not agent:
        return {"error": "Agent not found"}

    # Get their memories too
    memories = engine.state.memory_streams[agent_id].get_recent(limit=10)

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
        "current_activity": agent.get_current_activity(engine.state.clock.hour).activity,
        "location": agent.get_location(engine.state.clock.hour),
    }


@app.post("/inject")
async def inject_event_endpoint(event: dict):
    """Inject an event into the simulation"""
    content = event.get("content")
    if not content:
        return {"error": "Missing 'content' field"}

    # Run in thread pool so it doesn't block - allows broadcasts during processing
    loop = asyncio.get_event_loop()
    injected = await loop.run_in_executor(None, engine.inject_event, content)

    return {
        "success": True,
        "event_id": injected.id,
        "content": injected.content,
    }


@app.get("/feed")
async def get_feed():
    """Get live feed items"""
    return {"feed": engine.state.feed_items[:50]}


# =============================================================================
# WebSocket
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)

    # Send initial state
    try:
        await websocket.send_json({
            "type": "initial_state",
            "data": get_state_snapshot()
        })
    except Exception as e:
        print(f"Error sending initial state: {e}")

    # Keep connection alive and handle incoming messages
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle client messages
            if message.get("type") == "inject":
                content = message.get("content")
                if content:
                    # Run in thread so broadcasts can happen during processing
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, engine.inject_event, content)

            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
