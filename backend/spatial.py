"""
Spatial System - Tile-based movement like Generative Agents

Key concepts from Stanford's Generative Agents:
1. Tiles have events - agents are tracked as events on tiles
2. BFS pathfinding - wave expansion to find shortest path
3. Collision check - look at tile events before moving
"""

from dataclasses import dataclass, field
from typing import Optional, Set, Tuple, List, Dict
import random

TILE_SIZE = 32  # Match generative_agents
GRID_W, GRID_H = 28, 19

# Location tile areas (x_min, x_max, y_min, y_max)
LOCATIONS = {
    "home-maple": (2, 7, 2, 6),
    "sunset-flats": (10, 15, 2, 6),
    "cafe-luma": (19, 24, 2, 6),
    "civic-office": (11, 15, 8, 10),
    "brookside-school": (18, 24, 9, 12),
    "corner-mart": (2, 8, 12, 15),
    "meadow-park": (10, 17, 13, 16),
}

LOCATION_ALIASES = {
    "home": "home-maple", "apartment": "sunset-flats", "flats": "sunset-flats",
    "cafe": "cafe-luma", "café": "cafe-luma", "coffee shop": "cafe-luma",
    "office": "civic-office", "work": "civic-office", "workplace": "civic-office",
    "school": "brookside-school", "university": "brookside-school", "library": "brookside-school",
    "shop": "corner-mart", "store": "corner-mart", "market": "corner-mart",
    "park": "meadow-park", "outside": "meadow-park", "garden": "meadow-park",
}


def resolve_location(s: str) -> Optional[str]:
    """Resolve location string to location ID"""
    s = s.lower().strip()
    if s in LOCATIONS:
        return s
    if s in LOCATION_ALIASES:
        return LOCATION_ALIASES[s]
    for alias, loc_id in LOCATION_ALIASES.items():
        if alias in s or s in alias:
            return loc_id
    return None


class Maze:
    """
    Tile-based maze like Generative Agents.

    Key feature: Each tile has an 'events' set that tracks what's on it.
    Agents are tracked as events: ("persona", agent_id, None)
    """

    def __init__(self):
        self.width = GRID_W
        self.height = GRID_H
        self.tile_size = TILE_SIZE

        # Initialize tiles - each tile has events set and collision info
        # tiles[y][x] to match generative_agents convention
        self.tiles: List[List[Dict]] = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                tile = {
                    "collision": False,  # No collision blocks in our simple map
                    "events": set(),      # Set of events: (type, id, data)
                    "location_id": self._get_location_for_tile(x, y),
                }
                row.append(tile)
            self.tiles.append(row)

        # Reverse lookup: location_id -> set of (x, y) tiles
        self.location_tiles: Dict[str, Set[Tuple[int, int]]] = {}
        for loc_id, (x1, x2, y1, y2) in LOCATIONS.items():
            self.location_tiles[loc_id] = set()
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.location_tiles[loc_id].add((x, y))

    def _get_location_for_tile(self, x: int, y: int) -> Optional[str]:
        """Get which location a tile belongs to"""
        for loc_id, (x1, x2, y1, y2) in LOCATIONS.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return loc_id
        return None

    def access_tile(self, x: int, y: int) -> Optional[Dict]:
        """Get tile at (x, y)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def add_event_to_tile(self, event: Tuple, x: int, y: int):
        """Add an event to a tile"""
        tile = self.access_tile(x, y)
        if tile:
            tile["events"].add(event)

    def remove_event_from_tile(self, event: Tuple, x: int, y: int):
        """Remove an event from a tile"""
        tile = self.access_tile(x, y)
        if tile and event in tile["events"]:
            tile["events"].discard(event)

    def remove_agent_from_tile(self, agent_id: str, x: int, y: int):
        """Remove an agent's event from a tile"""
        tile = self.access_tile(x, y)
        if tile:
            to_remove = [e for e in tile["events"] if e[0] == "persona" and e[1] == agent_id]
            for e in to_remove:
                tile["events"].discard(e)

    def is_tile_occupied_by_other(self, agent_id: str, x: int, y: int) -> bool:
        """Check if tile has another persona on it"""
        tile = self.access_tile(x, y)
        if not tile:
            return True  # Out of bounds = occupied

        for event in tile["events"]:
            if event[0] == "persona" and event[1] != agent_id:
                return True  # Another persona is here
        return False

    def get_agent_on_tile(self, x: int, y: int) -> Optional[str]:
        """Get the agent ID on a tile, if any"""
        tile = self.access_tile(x, y)
        if tile:
            for event in tile["events"]:
                if event[0] == "persona":
                    return event[1]
        return None

    def get_free_tile_in_location(self, loc_id: str, agent_id: str) -> Optional[Tuple[int, int]]:
        """Find a free tile in a location for an agent"""
        if loc_id not in self.location_tiles:
            return (14, 9)  # Fallback to center

        tiles = list(self.location_tiles[loc_id])

        # Shuffle deterministically per agent
        rng = random.Random(hash(agent_id) + hash(loc_id))
        rng.shuffle(tiles)

        # Find first free tile
        for (x, y) in tiles:
            if not self.is_tile_occupied_by_other(agent_id, x, y):
                return (x, y)

        # All occupied - return first tile anyway
        return tiles[0] if tiles else (14, 9)


# Global maze instance
maze = Maze()


def path_finder_bfs(start: Tuple[int, int], end: Tuple[int, int], agent_id: str) -> List[Tuple[int, int]]:
    """
    BFS pathfinding like generative_agents path_finder_v2.

    Uses wave expansion to find shortest path from start to end.
    Avoids tiles with other agents.
    """
    if start == end:
        return [start]

    # Distance map: -1 = unvisited, 0+ = distance from start
    dist = [[-1 for _ in range(maze.width)] for _ in range(maze.height)]

    sx, sy = start
    ex, ey = end

    # BFS from start
    dist[sy][sx] = 0
    queue = [(sx, sy)]
    qi = 0

    while qi < len(queue):
        cx, cy = queue[qi]
        qi += 1

        if (cx, cy) == end:
            break

        d = dist[cy][cx]

        # Check all 4 neighbors
        for nx, ny in [(cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)]:
            if 0 <= nx < maze.width and 0 <= ny < maze.height:
                if dist[ny][nx] == -1:  # Unvisited
                    tile = maze.access_tile(nx, ny)
                    if tile and not tile["collision"]:
                        # Allow if it's our destination or unoccupied
                        if (nx, ny) == end or not maze.is_tile_occupied_by_other(agent_id, nx, ny):
                            dist[ny][nx] = d + 1
                            queue.append((nx, ny))

    # Check if we reached the end
    if dist[ey][ex] == -1:
        # No path found - just return start
        return [start]

    # Trace back from end to start
    path = [(ex, ey)]
    cx, cy = ex, ey

    while (cx, cy) != start:
        d = dist[cy][cx]
        # Find neighbor with distance d-1
        for nx, ny in [(cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)]:
            if 0 <= nx < maze.width and 0 <= ny < maze.height:
                if dist[ny][nx] == d - 1:
                    path.append((nx, ny))
                    cx, cy = nx, ny
                    break

    path.reverse()
    return path


@dataclass
class AgentSpatialState:
    """Spatial state for an agent"""
    agent_id: str
    x: int  # Current tile x
    y: int  # Current tile y
    target_x: int  # Destination tile x
    target_y: int  # Destination tile y
    location_id: str = ""
    path: List[Tuple[int, int]] = field(default_factory=list)
    path_index: int = 0

    def to_dict(self) -> dict:
        """Convert to frontend format (tile coordinates - frontend handles pixel conversion)"""
        return {
            "x": self.x,
            "y": self.y,
            "target_x": self.target_x,
            "target_y": self.target_y,
            "location_id": self.location_id,
        }


def initialize_agent_position(agent_id: str, loc_id: str) -> AgentSpatialState:
    """Initialize an agent's position in a location"""
    # Find a free tile
    tile = maze.get_free_tile_in_location(loc_id, agent_id)
    x, y = tile if tile else (14, 9)

    # Add agent to tile as event
    maze.add_event_to_tile(("persona", agent_id, None), x, y)

    return AgentSpatialState(
        agent_id=agent_id,
        x=x, y=y,
        target_x=x, target_y=y,
        location_id=loc_id,
    )


def move_agent_one_step(spatial: AgentSpatialState) -> bool:
    """
    Move agent one step along their path.

    Returns True if agent moved, False if blocked or at destination.
    """
    # At destination?
    if spatial.x == spatial.target_x and spatial.y == spatial.target_y:
        return False

    # Need to calculate path?
    if not spatial.path or spatial.path_index >= len(spatial.path):
        spatial.path = path_finder_bfs(
            (spatial.x, spatial.y),
            (spatial.target_x, spatial.target_y),
            spatial.agent_id
        )
        spatial.path_index = 1  # Start at index 1 (0 is current position)

    # No more path?
    if spatial.path_index >= len(spatial.path):
        return False

    # Get next tile
    next_x, next_y = spatial.path[spatial.path_index]

    # Check if next tile is blocked by another agent
    if maze.is_tile_occupied_by_other(spatial.agent_id, next_x, next_y):
        # Blocked! Clear path to recalculate next tick
        spatial.path = []
        spatial.path_index = 0
        return False

    # Move!
    old_x, old_y = spatial.x, spatial.y

    # Remove from old tile
    maze.remove_agent_from_tile(spatial.agent_id, old_x, old_y)

    # Update position
    spatial.x = next_x
    spatial.y = next_y
    spatial.path_index += 1

    # Add to new tile
    maze.add_event_to_tile(("persona", spatial.agent_id, None), next_x, next_y)

    return True


def set_agent_target(spatial: AgentSpatialState, target_loc_id: str) -> bool:
    """
    Set a new target location for an agent.

    Returns True if target was set, False if same location.
    """
    if spatial.location_id == target_loc_id:
        return False

    # Find a free tile at target location
    tile = maze.get_free_tile_in_location(target_loc_id, spatial.agent_id)
    if not tile:
        return False

    spatial.target_x, spatial.target_y = tile
    spatial.location_id = target_loc_id
    spatial.path = []  # Clear path to recalculate
    spatial.path_index = 0

    return True


# Debug function
def print_agent_positions():
    """Print all agent positions for debugging"""
    agents = {}
    for y in range(maze.height):
        for x in range(maze.width):
            tile = maze.tiles[y][x]
            for event in tile["events"]:
                if event[0] == "persona":
                    agents[event[1]] = (x, y)

    print(f"Agent positions ({len(agents)} agents):")
    for aid, (x, y) in sorted(agents.items()):
        print(f"  {aid}: ({x}, {y})")

    # Check for overlaps
    positions = list(agents.values())
    unique = set(positions)
    if len(positions) != len(unique):
        print(f"WARNING: {len(positions) - len(unique)} overlapping positions!")
    else:
        print(f"OK: All {len(agents)} agents on unique tiles")


# For backwards compatibility with existing engine.py imports
def find_free_tile(loc_id: str, agent_id: str) -> Tuple[int, int]:
    """Backwards compatible function"""
    tile = maze.get_free_tile_in_location(loc_id, agent_id)
    return tile if tile else (14, 9)


def claim_tile(agent_id: str, x: int, y: int) -> bool:
    """Backwards compatible function - check and claim a tile"""
    if maze.is_tile_occupied_by_other(agent_id, x, y):
        return False

    # Remove from any old tile
    for ty in range(maze.height):
        for tx in range(maze.width):
            maze.remove_agent_from_tile(agent_id, tx, ty)

    # Add to new tile
    maze.add_event_to_tile(("persona", agent_id, None), x, y)
    return True


# =============================================================================
# Spatial Awareness - Agents perceive nearby agents
# =============================================================================

VISION_RADIUS = 5  # Tiles an agent can "see"


def get_agent_position(agent_id: str) -> Optional[Tuple[int, int]]:
    """Get an agent's current position"""
    for y in range(maze.height):
        for x in range(maze.width):
            tile = maze.tiles[y][x]
            for event in tile["events"]:
                if event[0] == "persona" and event[1] == agent_id:
                    return (x, y)
    return None


def get_nearby_agents(agent_id: str, radius: int = VISION_RADIUS) -> List[Tuple[str, int, int, float]]:
    """
    Find agents within vision radius of an agent.

    Returns:
        List of (other_agent_id, x, y, distance) tuples, sorted by distance
    """
    pos = get_agent_position(agent_id)
    if not pos:
        return []

    ax, ay = pos
    nearby = []

    # Check all tiles within radius
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            x, y = ax + dx, ay + dy

            # Skip out of bounds
            if not (0 <= x < maze.width and 0 <= y < maze.height):
                continue

            # Calculate distance
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > radius:
                continue

            # Check for agents on this tile
            tile = maze.tiles[y][x]
            for event in tile["events"]:
                if event[0] == "persona" and event[1] != agent_id:
                    nearby.append((event[1], x, y, dist))

    # Sort by distance
    nearby.sort(key=lambda x: x[3])
    return nearby


def get_agents_at_same_location(agent_id: str, spatial_states: Dict[str, 'AgentSpatialState']) -> List[str]:
    """
    Find agents at the same location as another agent.

    Args:
        agent_id: The agent to check
        spatial_states: Dict of agent_id -> AgentSpatialState

    Returns:
        List of agent IDs at the same location
    """
    if agent_id not in spatial_states:
        return []

    my_location = spatial_states[agent_id].location_id
    if not my_location:
        return []

    same_location = []
    for other_id, other_state in spatial_states.items():
        if other_id != agent_id and other_state.location_id == my_location:
            same_location.append(other_id)

    return same_location


def perceive_surroundings(
    agent_id: str,
    spatial_states: Dict[str, 'AgentSpatialState'],
    agent_activities: Dict[str, str] = None,
) -> List[Dict]:
    """
    Get what an agent can perceive around them.

    This is the main perception function that returns what the agent "sees".

    Args:
        agent_id: The perceiving agent
        spatial_states: Dict of all agent positions
        agent_activities: Optional dict of agent_id -> current activity

    Returns:
        List of perception dicts:
        [
            {"type": "agent", "agent_id": "klaus", "activity": "writing", "distance": 2.5},
            ...
        ]
    """
    perceptions = []

    # Get nearby agents
    nearby = get_nearby_agents(agent_id)

    for other_id, x, y, distance in nearby:
        perception = {
            "type": "agent",
            "agent_id": other_id,
            "distance": round(distance, 1),
            "x": x,
            "y": y,
        }

        # Add activity if known
        if agent_activities and other_id in agent_activities:
            perception["activity"] = agent_activities[other_id]

        # Add location if known
        if other_id in spatial_states:
            perception["location"] = spatial_states[other_id].location_id

        perceptions.append(perception)

    return perceptions


def get_proximity_pairs(spatial_states: Dict[str, 'AgentSpatialState'], max_distance: int = 3) -> List[Tuple[str, str, float]]:
    """
    Get all pairs of agents that are close to each other.

    Useful for frontend to draw proximity lines.

    Returns:
        List of (agent1_id, agent2_id, distance) tuples
    """
    pairs = []
    agent_ids = list(spatial_states.keys())

    for i, agent1_id in enumerate(agent_ids):
        nearby = get_nearby_agents(agent1_id, radius=max_distance)

        for other_id, x, y, distance in nearby:
            # Only add each pair once (agent1 < agent2 alphabetically)
            if agent1_id < other_id:
                pairs.append((agent1_id, other_id, distance))

    return pairs
