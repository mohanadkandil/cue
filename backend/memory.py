"""
Memory Stream & Retrieval System

Handles:
- Storing memories for each agent
- Retrieving relevant memories using recency + relevance + importance
- SEMANTIC matching using embeddings (finds related concepts, not just keywords)
"""

import math
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from sentence_transformers import SentenceTransformer

# Load embedding model ONCE (shared across all agents)
# all-MiniLM-L6-v2: Small (80MB), fast, good quality
print("Loading embedding model...")
_EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding model loaded!")


@dataclass
class Memory:
    """A single memory in an agent's memory stream"""
    id: str
    created_at: datetime
    content: str
    memory_type: str  # "observation", "conversation", "thought", "reaction", "reflection"
    poignancy: int = 5  # 1-10, emotional importance
    related_event_id: str = None
    related_agent_id: str = None
    last_accessed: datetime = None  # Updated when retrieved

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


class MemoryStream:
    """
    Manages all memories for a single agent.
    Uses SEMANTIC retrieval (embeddings) instead of keyword matching.

    How it works:
    1. When memory added → generate embedding vector, store both
    2. When retrieving → embed query, find similar memories by vector similarity
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memories: list[Memory] = []
        self.embeddings: list[np.ndarray] = []  # Parallel list of embedding vectors
        self._memory_counter = 0

    def add(
        self,
        content: str,
        memory_type: str,
        poignancy: int = 5,
        related_event_id: str = None,
        related_agent_id: str = None,
    ) -> Memory:
        """
        Add a new memory to the stream.

        Generates embedding at creation time (only once).
        """
        self._memory_counter += 1
        memory = Memory(
            id=f"{self.agent_id}-mem-{self._memory_counter}",
            created_at=datetime.now(),
            content=content,
            memory_type=memory_type,
            poignancy=poignancy,
            related_event_id=related_event_id,
            related_agent_id=related_agent_id,
        )

        # Generate embedding for this memory (ONCE, right now)
        embedding = _EMBEDDING_MODEL.encode(content, convert_to_numpy=True)

        # Store both
        self.memories.append(memory)
        self.embeddings.append(embedding)

        return memory

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        recency_weight: float = 1.0,
        relevance_weight: float = 1.0,
        importance_weight: float = 1.0,
    ) -> list[Memory]:
        """
        Retrieve most relevant memories for a query using SEMANTIC search.

        Scoring formula:
            score = (recency * w1) + (semantic_similarity * w2) + (importance * w3)

        Args:
            query: The situation/event to find relevant memories for
            limit: Max number of memories to return
            recency_weight: How much to weight recent memories
            relevance_weight: How much to weight semantic similarity
            importance_weight: How much to weight poignancy

        Returns:
            List of top memories, sorted by score
        """
        if not self.memories:
            return []

        # Generate embedding for the query
        query_embedding = _EMBEDDING_MODEL.encode(query, convert_to_numpy=True)

        now = datetime.now()
        scored = []

        for i, memory in enumerate(self.memories):
            # 1. Recency score (exponential decay)
            hours_ago = (now - memory.created_at).total_seconds() / 3600
            recency = math.exp(-0.01 * hours_ago)  # Decay factor

            # 2. Relevance score (SEMANTIC similarity via embeddings)
            relevance = cosine_similarity(query_embedding, self.embeddings[i])
            # Normalize to 0-1 range (cosine sim can be -1 to 1, but usually 0-1 for text)
            relevance = max(0, relevance)

            # 3. Importance score (normalized poignancy)
            importance = memory.poignancy / 10.0

            # Combined score
            score = (
                recency * recency_weight +
                relevance * relevance_weight +
                importance * importance_weight
            )

            scored.append((score, memory))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Update last_accessed for retrieved memories
        results = []
        for score, memory in scored[:limit]:
            memory.last_accessed = now
            results.append(memory)

        return results

    def get_recent(self, limit: int = 10) -> list[Memory]:
        """Get most recent memories (simple recency, no scoring)"""
        return self.memories[-limit:]

    def get_by_type(self, memory_type: str) -> list[Memory]:
        """Get all memories of a specific type"""
        return [m for m in self.memories if m.memory_type == memory_type]

    def get_about_event(self, event_id: str) -> list[Memory]:
        """Get all memories related to a specific event"""
        return [m for m in self.memories if m.related_event_id == event_id]

    def get_about_agent(self, agent_id: str) -> list[Memory]:
        """Get all memories involving another agent"""
        return [m for m in self.memories if m.related_agent_id == agent_id]

    def count(self) -> int:
        """Total number of memories"""
        return len(self.memories)

    def summarize(self) -> dict:
        """Get summary stats about this memory stream"""
        types = {}
        for m in self.memories:
            types[m.memory_type] = types.get(m.memory_type, 0) + 1

        return {
            "total": len(self.memories),
            "by_type": types,
            "avg_poignancy": sum(m.poignancy for m in self.memories) / len(self.memories) if self.memories else 0,
        }


# Test when run directly
if __name__ == "__main__":
    print("\nMemory Stream Demo (with Embeddings)\n")
    print("=" * 50)

    # Create memory stream for Elena
    stream = MemoryStream("agent-01")

    # Add some memories
    print("Adding memories...")
    stream.add(
        "Signed up for NovaCRM to manage café customers",
        memory_type="observation",
        poignancy=6,
    )
    stream.add(
        "Had coffee with Liam, talked about the weekend",
        memory_type="conversation",
        poignancy=4,
        related_agent_id="agent-12",
    )
    stream.add(
        "Complained to Marco about rising software costs",
        memory_type="conversation",
        poignancy=7,
        related_agent_id="agent-02",
    )
    stream.add(
        "Morning rush was busy, served 50 customers",
        memory_type="observation",
        poignancy=5,
    )
    stream.add(
        "Business expenses are getting out of hand",
        memory_type="thought",
        poignancy=6,
    )
    stream.add(
        "Marco mentioned he's evaluating cheaper alternatives",
        memory_type="conversation",
        poignancy=6,
        related_agent_id="agent-02",
    )

    print(f"\nElena has {stream.count()} memories\n")

    # Test SEMANTIC retrieval
    print("=" * 50)
    print("SEMANTIC Retrieval Test")
    print("=" * 50)

    query = "pricing concerns and money problems"
    print(f"\nQuery: '{query}'")
    print("-" * 50)

    results = stream.retrieve(query, limit=4)
    for i, mem in enumerate(results, 1):
        # Calculate similarity for display
        query_emb = _EMBEDDING_MODEL.encode(query, convert_to_numpy=True)
        mem_emb = stream.embeddings[stream.memories.index(mem)]
        sim = cosine_similarity(query_emb, mem_emb)

        print(f"{i}. [{mem.memory_type}] {mem.content}")
        print(f"   Similarity: {sim:.2f} | Poignancy: {mem.poignancy}")
        print()

    # Compare with a different query
    print("=" * 50)
    query2 = "social activities with friends"
    print(f"\nQuery: '{query2}'")
    print("-" * 50)

    results2 = stream.retrieve(query2, limit=3)
    for i, mem in enumerate(results2, 1):
        query_emb = _EMBEDDING_MODEL.encode(query2, convert_to_numpy=True)
        mem_emb = stream.embeddings[stream.memories.index(mem)]
        sim = cosine_similarity(query_emb, mem_emb)

        print(f"{i}. [{mem.memory_type}] {mem.content}")
        print(f"   Similarity: {sim:.2f} | Poignancy: {mem.poignancy}")
        print()
