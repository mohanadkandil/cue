"""
Memory Stream & Retrieval System

Handles:
- Storing memories for each agent
- Retrieving relevant memories using recency + relevance + importance
- Keyword-based matching (no embeddings needed)
"""

import re
import math
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Memory:
    """A single memory in an agent's memory stream"""
    id: str
    created_at: datetime
    content: str
    memory_type: str  # "observation", "conversation", "thought", "reaction"
    poignancy: int = 5  # 1-10, emotional importance
    keywords: list[str] = field(default_factory=list)  # For retrieval
    related_event_id: str = None
    related_agent_id: str = None
    last_accessed: datetime = None  # Updated when retrieved

    def __post_init__(self):
        # Auto-extract keywords if not provided
        if not self.keywords:
            self.keywords = extract_keywords(self.content)
        # Set last_accessed to creation time initially
        if self.last_accessed is None:
            self.last_accessed = self.created_at


def extract_keywords(text: str) -> list[str]:
    """
    Extract keywords from text for matching.
    Simple approach: lowercase words, remove common words.
    """
    # Common words to ignore
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "can", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after",
        "above", "below", "between", "under", "again", "further",
        "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "and", "but", "if", "or",
        "because", "until", "while", "about", "against", "between",
        "into", "through", "during", "before", "after", "above",
        "below", "up", "down", "out", "off", "over", "under", "again",
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
        "you", "your", "yours", "yourself", "he", "him", "his",
        "himself", "she", "her", "hers", "herself", "it", "its",
        "itself", "they", "them", "their", "theirs", "themselves",
        "what", "which", "who", "whom", "this", "that", "these",
        "those", "am", "been", "being", "having", "doing",
    }

    # Extract words, lowercase, filter
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    keywords = [w for w in words if w not in stopwords]

    # Remove duplicates, keep order
    seen = set()
    unique = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique.append(w)

    return unique


class MemoryStream:
    """
    Manages all memories for a single agent.
    Provides retrieval based on recency, relevance, and importance.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memories: list[Memory] = []
        self._memory_counter = 0

    def add(
        self,
        content: str,
        memory_type: str,
        poignancy: int = 5,
        keywords: list[str] = None,
        related_event_id: str = None,
        related_agent_id: str = None,
    ) -> Memory:
        """Add a new memory to the stream"""
        self._memory_counter += 1
        memory = Memory(
            id=f"{self.agent_id}-mem-{self._memory_counter}",
            created_at=datetime.now(),
            content=content,
            memory_type=memory_type,
            poignancy=poignancy,
            keywords=keywords or [],
            related_event_id=related_event_id,
            related_agent_id=related_agent_id,
        )
        self.memories.append(memory)
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
        Retrieve most relevant memories for a query.

        Scoring formula:
            score = (recency * w1) + (relevance * w2) + (importance * w3)

        Args:
            query: The situation/event to find relevant memories for
            limit: Max number of memories to return
            recency_weight: How much to weight recent memories
            relevance_weight: How much to weight keyword matches
            importance_weight: How much to weight poignancy

        Returns:
            List of top memories, sorted by score
        """
        if not self.memories:
            return []

        query_keywords = set(extract_keywords(query))
        now = datetime.now()
        scored = []

        for memory in self.memories:
            # 1. Recency score (exponential decay)
            hours_ago = (now - memory.created_at).total_seconds() / 3600
            recency = math.exp(-0.01 * hours_ago)  # Decay factor

            # 2. Relevance score (keyword overlap)
            memory_keywords = set(memory.keywords)
            if query_keywords and memory_keywords:
                overlap = len(query_keywords & memory_keywords)
                relevance = overlap / len(query_keywords)
            else:
                relevance = 0.0

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
    print("Memory Stream Demo\n")
    print("=" * 50)

    # Create memory stream for Elena
    stream = MemoryStream("agent-01")

    # Add some memories (simulating a few days)
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
        "Read article about SaaS pricing trends",
        memory_type="observation",
        poignancy=4,
    )
    stream.add(
        "Marco mentioned he's evaluating CRM alternatives",
        memory_type="conversation",
        poignancy=6,
        related_agent_id="agent-02",
    )

    print(f"Elena has {stream.count()} memories\n")

    # Test keyword extraction
    print("Keyword extraction test:")
    test_text = "NovaCRM raised prices by 40% effective next month"
    keywords = extract_keywords(test_text)
    print(f"  Text: {test_text}")
    print(f"  Keywords: {keywords}\n")

    # Test retrieval
    print("Retrieval test - Query: 'NovaCRM price increase'")
    print("-" * 50)
    results = stream.retrieve("NovaCRM price increase", limit=3)
    for i, mem in enumerate(results, 1):
        print(f"{i}. [{mem.memory_type}] {mem.content}")
        print(f"   Keywords: {mem.keywords}")
        print(f"   Poignancy: {mem.poignancy}")
        print()

    # Show summary
    print("Memory stream summary:")
    print(stream.summarize())
