"""
Cognition Module - LLM Integration

Handles all LLM calls for:
- Generating agent reactions to events
- Generating conversations between agents
- Generating agent thoughts/reflections

Uses OpenRouter API with structured outputs for guaranteed JSON responses.
"""

import os
import json
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "minimax/minimax-m2.5"


# ============================================================================
# JSON Schemas for Structured Outputs
# ============================================================================

REACTION_SCHEMA = {
    "name": "agent_reaction",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "thought": {
                "type": "string",
                "description": "The agent's inner monologue reaction (2-3 sentences, first person)"
            },
            "sentiment": {
                "type": "string",
                "enum": ["positive", "negative", "neutral"],
                "description": "How the agent feels about this event"
            },
            "would_share": {
                "type": "boolean",
                "description": "Whether the agent would tell others about this"
            },
            "share_summary": {
                "type": "string",
                "description": "One sentence summary they'd tell others (or empty if not sharing)"
            }
        },
        "required": ["thought", "sentiment", "would_share", "share_summary"],
        "additionalProperties": False
    }
}

# Poll reaction schema - more granular sentiments for instant feedback
POLL_REACTION_SCHEMA = {
    "name": "poll_reaction",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "thought": {
                "type": "string",
                "description": "The agent's brief reaction (1-2 sentences, first person)"
            },
            "sentiment": {
                "type": "string",
                "enum": ["positive", "curious", "skeptical", "negative"],
                "description": "How the agent feels: positive (excited/happy), curious (interested/want to know more), skeptical (uncertain/doubting), negative (opposed/unhappy)"
            },
            "intensity": {
                "type": "integer",
                "description": "How strongly they feel (1-5, where 5 is strongest)"
            }
        },
        "required": ["thought", "sentiment", "intensity"],
        "additionalProperties": False
    }
}

# Poll summary schema - for generating aggregate insight
POLL_SUMMARY_SCHEMA = {
    "name": "poll_summary",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "key_insight": {
                "type": "string",
                "description": "A 2-3 sentence summary of the overall sentiment and key themes from all responses"
            },
            "notable_themes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5 key themes or concerns that emerged from the responses"
            }
        },
        "required": ["key_insight", "notable_themes"],
        "additionalProperties": False
    }
}

CONVERSATION_SCHEMA = {
    "name": "agent_conversation",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "exchanges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "speaker": {
                            "type": "string",
                            "description": "Name of the person speaking"
                        },
                        "message": {
                            "type": "string",
                            "description": "What they said"
                        }
                    },
                    "required": ["speaker", "message"],
                    "additionalProperties": False
                },
                "description": "List of conversation exchanges"
            },
            "topic": {
                "type": "string",
                "description": "Brief summary of what they discussed"
            },
            "mood": {
                "type": "string",
                "enum": ["friendly", "tense", "casual", "excited", "concerned"],
                "description": "Overall mood of the conversation"
            }
        },
        "required": ["exchanges", "topic", "mood"],
        "additionalProperties": False
    }
}

THOUGHT_SCHEMA = {
    "name": "agent_thought",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "thought": {
                "type": "string",
                "description": "A brief inner thought (one sentence, first person)"
            }
        },
        "required": ["thought"],
        "additionalProperties": False
    }
}

ACTION_SCHEMA = {
    "name": "agent_action",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "chosen_action": {
                "type": "string",
                "description": "The action the agent chooses to take"
            },
            "reason": {
                "type": "string",
                "description": "Brief reason for this choice"
            }
        },
        "required": ["chosen_action", "reason"],
        "additionalProperties": False
    }
}

# Daily plan schema - for generating personalized schedules
DAILY_PLAN_SCHEMA = {
    "name": "daily_plan",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "wake_up_hour": {
                "type": "integer",
                "description": "Hour they wake up (5-9)"
            },
            "sleep_hour": {
                "type": "integer",
                "description": "Hour they go to sleep (21-24)"
            },
            "schedule": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "hour": {
                            "type": "integer",
                            "description": "Start hour (0-23)"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration in hours (1-4)"
                        },
                        "activity": {
                            "type": "string",
                            "description": "What they're doing"
                        },
                        "location": {
                            "type": "string",
                            "description": "Where they're doing it"
                        },
                        "can_be_interrupted": {
                            "type": "boolean",
                            "description": "Can others interrupt them?"
                        }
                    },
                    "required": ["hour", "duration", "activity", "location", "can_be_interrupted"],
                    "additionalProperties": False
                },
                "description": "List of scheduled activities for the day"
            }
        },
        "required": ["wake_up_hour", "sleep_hour", "schedule"],
        "additionalProperties": False
    }
}

# Task decomposition schema - break hourly blocks into smaller tasks
TASK_DECOMPOSITION_SCHEMA = {
    "name": "task_decomposition",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "subtasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start_minute": {
                            "type": "integer",
                            "description": "Start minute within the hour (0-59)"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Duration in minutes (5-30)"
                        },
                        "subtask": {
                            "type": "string",
                            "description": "Specific action being performed"
                        }
                    },
                    "required": ["start_minute", "duration_minutes", "subtask"],
                    "additionalProperties": False
                },
                "description": "Breakdown of the activity into smaller tasks"
            }
        },
        "required": ["subtasks"],
        "additionalProperties": False
    }
}

# Reflection schema - for generating insights from memories
REFLECTION_SCHEMA = {
    "name": "agent_reflection",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "insights": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "insight": {
                            "type": "string",
                            "description": "A higher-level observation or pattern noticed (first person)"
                        },
                        "importance": {
                            "type": "integer",
                            "description": "How important is this insight (1-10)"
                        }
                    },
                    "required": ["insight", "importance"],
                    "additionalProperties": False
                },
                "description": "List of insights derived from recent memories"
            }
        },
        "required": ["insights"],
        "additionalProperties": False
    }
}


# ============================================================================
# Agent Context
# ============================================================================

@dataclass
class AgentContext:
    """Context about an agent for LLM prompts"""
    name: str
    age: int
    occupation: str
    bio: str
    personality_summary: str
    biases: list[str]
    current_activity: str
    current_location: str
    relevant_memories: list[str]


def build_personality_summary(personality: dict) -> str:
    """Convert personality scores to readable description"""
    traits = []

    if personality["extraversion"] > 70:
        traits.append("extraverted")
    elif personality["extraversion"] < 40:
        traits.append("introverted")

    if personality["agreeableness"] > 70:
        traits.append("agreeable")
    elif personality["agreeableness"] < 40:
        traits.append("disagreeable")

    if personality["openness"] > 70:
        traits.append("open-minded")
    elif personality["openness"] < 40:
        traits.append("traditional")

    if personality["neuroticism"] > 70:
        traits.append("anxious")
    elif personality["neuroticism"] < 40:
        traits.append("calm")

    if personality["conscientiousness"] > 70:
        traits.append("organized")
    elif personality["conscientiousness"] < 40:
        traits.append("spontaneous")

    return ", ".join(traits) if traits else "balanced"


# ============================================================================
# LLM Call Helper
# ============================================================================

def _call_llm(
    system_prompt: str,
    user_prompt: str,
    response_schema: dict,
    max_tokens: int = 300
) -> dict:
    """
    Make a call to the LLM via OpenRouter with structured output.

    Returns:
        Parsed JSON response as dict
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.8,
            response_format={
                "type": "json_schema",
                "json_schema": response_schema
            }
        )

        content = response.choices[0].message.content

        # Handle None content
        if content is None:
            print(f"Warning: LLM returned None content")
            return None

        return json.loads(content)

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw content was: {content}")
        return None
    except Exception as e:
        print(f"LLM call failed: {e}")
        return None


# ============================================================================
# Cognition Functions
# ============================================================================

def generate_reaction(
    agent_context: AgentContext,
    event: str,
) -> dict:
    """
    Generate an agent's reaction to an event.

    Returns:
        {
            "thought": "The agent's inner monologue",
            "sentiment": "positive" | "negative" | "neutral",
            "would_share": True | False,
            "share_summary": "What they'd tell others"
        }
    """
    system_prompt = """You are simulating the inner thoughts of a person in a social simulation.
Respond in first person as this character. Be authentic to their personality and biases.
Keep thoughts concise (2-3 sentences)."""

    memories_text = "\n".join(f"- {m}" for m in agent_context.relevant_memories) if agent_context.relevant_memories else "No relevant memories."

    user_prompt = f"""Character: {agent_context.name}, {agent_context.age}, {agent_context.occupation}
Bio: {agent_context.bio}
Personality: {agent_context.personality_summary}
Biases: {", ".join(agent_context.biases)}
Currently: {agent_context.current_activity} at {agent_context.current_location}

Relevant memories:
{memories_text}

Event they just heard about: {event}

Generate their reaction."""

    result = _call_llm(system_prompt, user_prompt, REACTION_SCHEMA, max_tokens=300)

    if result is None:
        return {
            "thought": "...",
            "sentiment": "neutral",
            "would_share": False,
            "share_summary": ""
        }

    return result


def generate_poll_reaction(
    agent_context: AgentContext,
    event: str,
) -> dict:
    """
    Generate a quick poll reaction from an agent.

    Faster than full reaction - just sentiment and brief thought.
    Uses expanded sentiment categories: positive, curious, skeptical, negative.

    Returns:
        {
            "thought": "Brief reaction",
            "sentiment": "positive" | "curious" | "skeptical" | "negative",
            "intensity": 1-5
        }
    """
    system_prompt = """You are simulating a person's instant gut reaction to news.
Respond in first person. Keep it brief (1-2 sentences).
Be authentic to their personality and background."""

    user_prompt = f"""Character: {agent_context.name}, {agent_context.age}, {agent_context.occupation}
Bio: {agent_context.bio}
Personality: {agent_context.personality_summary}

News/Announcement: {event}

What's their immediate reaction? Choose sentiment:
- positive: excited, happy, supportive
- curious: interested, wants to know more, open but uncertain
- skeptical: doubtful, questioning, needs convincing
- negative: opposed, unhappy, against it"""

    result = _call_llm(system_prompt, user_prompt, POLL_REACTION_SCHEMA, max_tokens=150)

    if result is None:
        # Generate a simple fallback based on personality
        fallbacks = [
            "I need to think about how this affects my work.",
            "This could change things for people like me.",
            "I'm not sure what to make of this yet.",
            "Interesting - I'll be watching how this plays out.",
        ]
        import random
        return {
            "thought": random.choice(fallbacks),
            "sentiment": "curious",
            "intensity": 3
        }

    # Validate thought isn't empty
    if not result.get("thought") or result["thought"].strip() in ("", "..."):
        result["thought"] = "I'm still processing what this means for me."

    return result


def generate_poll_summary(
    event: str,
    reactions: list[dict],
    sentiment_counts: dict,
) -> dict:
    """
    Generate a summary insight from all poll reactions.

    Args:
        event: The original event/announcement
        reactions: List of reaction dicts with agent_name, thought, sentiment
        sentiment_counts: Dict of sentiment -> count

    Returns:
        {
            "key_insight": "Summary paragraph",
            "notable_themes": ["theme1", "theme2", ...]
        }
    """
    system_prompt = """You are analyzing feedback from a community of people.
Summarize the overall sentiment and identify key themes.
Be concise but insightful. Focus on actionable insights."""

    # Build reactions summary
    reactions_text = "\n".join([
        f"- {r['agent_name']} ({r['occupation']}, {r['sentiment']}): \"{r['thought']}\""
        for r in reactions[:15]  # Sample of reactions
    ])

    total = sum(sentiment_counts.values())
    pct = {k: round(v / total * 100) if total > 0 else 0 for k, v in sentiment_counts.items()}

    user_prompt = f"""Announcement: {event}

Sentiment breakdown ({total} respondents):
- Positive: {pct.get('positive', 0)}%
- Curious: {pct.get('curious', 0)}%
- Skeptical: {pct.get('skeptical', 0)}%
- Negative: {pct.get('negative', 0)}%

Sample reactions:
{reactions_text}

Provide a key insight (2-3 sentences summarizing the overall response and main concerns/excitement) and identify 3-5 notable themes."""

    result = _call_llm(system_prompt, user_prompt, POLL_SUMMARY_SCHEMA, max_tokens=300)

    if result is None:
        return {
            "key_insight": f"The community had mixed reactions to this announcement. {pct.get('positive', 0)}% responded positively while {pct.get('skeptical', 0) + pct.get('negative', 0)}% expressed concerns.",
            "notable_themes": ["Mixed reception", "Need for more details"]
        }

    return result


def generate_conversation(
    agent1_context: AgentContext,
    agent2_context: AgentContext,
    topic: str = None,
) -> dict:
    """
    Generate a conversation between two agents.

    Returns:
        {
            "exchanges": [{"speaker": "...", "message": "..."}, ...],
            "topic": "What they discussed",
            "mood": "friendly" | "tense" | "casual" | "excited" | "concerned"
        }
    """
    system_prompt = """You are generating a realistic conversation between two people.
Keep it natural and brief (2-4 exchanges total). Match their personalities.
If someone has something important on their mind (from recent memories), they might naturally bring it up."""

    topic_text = f"They are discussing: {topic}" if topic else ""

    # Include recent memories if available
    mem1 = ""
    if agent1_context.relevant_memories:
        mem1 = f"On their mind: {'; '.join(agent1_context.relevant_memories)}"

    mem2 = ""
    if agent2_context.relevant_memories:
        mem2 = f"On their mind: {'; '.join(agent2_context.relevant_memories)}"

    user_prompt = f"""Person 1: {agent1_context.name}, {agent1_context.age}, {agent1_context.occupation}
Personality: {agent1_context.personality_summary}
Currently: {agent1_context.current_activity}
{mem1}

Person 2: {agent2_context.name}, {agent2_context.age}, {agent2_context.occupation}
Personality: {agent2_context.personality_summary}
Currently: {agent2_context.current_activity}
{mem2}

{topic_text}

Generate their conversation."""

    result = _call_llm(system_prompt, user_prompt, CONVERSATION_SCHEMA, max_tokens=500)

    if result is None:
        return {
            "exchanges": [
                {"speaker": agent1_context.name, "message": "Hey, how's it going?"},
                {"speaker": agent2_context.name, "message": "Pretty good, you?"},
            ],
            "topic": topic or "casual chat",
            "mood": "casual"
        }

    return result


def generate_thought(
    agent_context: AgentContext,
    situation: str,
) -> str:
    """
    Generate a simple thought/reflection for an agent.
    Used for ambient "thinking" during idle moments.

    Returns:
        The thought as a string
    """
    system_prompt = """You are simulating a person's brief inner thought.
Keep it to one sentence. Be authentic to their personality.
Respond with just the thought, nothing else."""

    user_prompt = f"""Character: {agent_context.name}, {agent_context.occupation}
Personality: {agent_context.personality_summary}
Situation: {situation}

What are they briefly thinking? (One sentence, first person)"""

    # For simple thoughts, skip structured output - just get raw text
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=100,
            temperature=0.8,
        )
        content = response.choices[0].message.content
        return content.strip() if content else "..."
    except Exception as e:
        print(f"Thought generation failed: {e}")
        return "..."


def generate_reflection(
    agent_context: AgentContext,
    recent_memories: list[str],
) -> list[dict]:
    """
    Generate reflections (insights) from recent memories.

    This is the key cognitive process that makes agents feel "alive" -
    they notice patterns in their experiences and form higher-level
    understanding, just like humans do.

    Example:
        Memories: ["Argued with Tom", "Tom complained again", "Tom looked stressed"]
        Insight: "Tom seems increasingly frustrated lately. I should check on him."

    Args:
        agent_context: The agent's personality and current state
        recent_memories: List of recent memory strings to reflect on

    Returns:
        List of insights: [{"insight": "...", "importance": 1-10}, ...]
    """
    if len(recent_memories) < 3:
        # Need at least a few memories to find patterns
        return []

    system_prompt = """You are simulating a person's inner reflection process.
Based on their recent experiences, identify patterns, realizations, or insights.
These should be things a real person might notice about their life, relationships, or feelings.
Respond in first person as this character. Generate 1-3 meaningful insights."""

    memories_text = "\n".join(f"- {m}" for m in recent_memories)

    user_prompt = f"""Character: {agent_context.name}, {agent_context.age}, {agent_context.occupation}
Personality: {agent_context.personality_summary}
Current situation: {agent_context.current_activity}

Recent experiences:
{memories_text}

What patterns or realizations might they notice? What insights about their life,
relationships, or the world around them? (1-3 insights, first person)"""

    result = _call_llm(system_prompt, user_prompt, REFLECTION_SCHEMA, max_tokens=400)

    if result is None:
        return []

    return result.get("insights", [])


def generate_daily_plan(
    agent_context: AgentContext,
    yesterday_summary: str = None,
    special_events: list[str] = None,
) -> dict:
    """
    Generate a personalized daily schedule for an agent.

    Unlike static schedules, this creates unique plans based on:
    - The agent's personality and occupation
    - What happened yesterday (from memories)
    - Any special events today

    Returns:
        {
            "wake_up_hour": 6,
            "sleep_hour": 22,
            "schedule": [
                {"hour": 6, "duration": 1, "activity": "Morning routine", "location": "Home", "can_be_interrupted": False},
                {"hour": 7, "duration": 3, "activity": "Open café", "location": "Hobbs Cafe", "can_be_interrupted": True},
                ...
            ]
        }
    """
    system_prompt = """You are generating a realistic daily schedule for a person.
Consider their occupation, personality, and any special circumstances.
Create a believable day with variety - not every day is exactly the same.
Include meals, work, social time, and personal activities."""

    yesterday_text = f"\nYesterday: {yesterday_summary}" if yesterday_summary else ""
    events_text = f"\nSpecial events today: {', '.join(special_events)}" if special_events else ""

    user_prompt = f"""Character: {agent_context.name}, {agent_context.age}, {agent_context.occupation}
Personality: {agent_context.personality_summary}
Bio: {agent_context.bio}
{yesterday_text}{events_text}

Generate their schedule for today. Include 6-10 activities covering their full day.
Each activity should have an hour (0-23), duration (1-4 hours), activity description,
location, and whether they can be interrupted."""

    result = _call_llm(system_prompt, user_prompt, DAILY_PLAN_SCHEMA, max_tokens=600)

    if result is None:
        # Fallback to basic schedule
        return {
            "wake_up_hour": 7,
            "sleep_hour": 22,
            "schedule": [
                {"hour": 7, "duration": 1, "activity": "Morning routine", "location": "Home", "can_be_interrupted": False},
                {"hour": 8, "duration": 4, "activity": "Working", "location": "Work", "can_be_interrupted": True},
                {"hour": 12, "duration": 1, "activity": "Lunch", "location": "Local café", "can_be_interrupted": True},
                {"hour": 13, "duration": 4, "activity": "Working", "location": "Work", "can_be_interrupted": True},
                {"hour": 18, "duration": 2, "activity": "Relaxing", "location": "Home", "can_be_interrupted": True},
                {"hour": 20, "duration": 2, "activity": "Dinner and evening", "location": "Home", "can_be_interrupted": False},
            ]
        }

    return result


def decompose_task(
    agent_context: AgentContext,
    activity: str,
    duration_minutes: int = 60,
) -> list[dict]:
    """
    Break down an hourly activity into smaller 5-15 minute subtasks.

    Example:
        Input: "Work on Valentine's party decorations" (60 min)
        Output: [
            {"start_minute": 0, "duration_minutes": 15, "subtask": "Get supplies from storage"},
            {"start_minute": 15, "duration_minutes": 20, "subtask": "Hang up streamers"},
            {"start_minute": 35, "duration_minutes": 15, "subtask": "Arrange centerpieces"},
            {"start_minute": 50, "duration_minutes": 10, "subtask": "Check overall setup"},
        ]
    """
    system_prompt = """You are breaking down a task into smaller, concrete subtasks.
Each subtask should be specific and actionable (5-30 minutes).
Make it realistic - what steps would a person actually take?"""

    user_prompt = f"""Character: {agent_context.name}, {agent_context.occupation}

Task: {activity}
Total time: {duration_minutes} minutes

Break this into 3-6 specific subtasks. Each subtask needs:
- start_minute: When it starts (0-{duration_minutes-5})
- duration_minutes: How long (5-30 min)
- subtask: What specifically they're doing"""

    result = _call_llm(system_prompt, user_prompt, TASK_DECOMPOSITION_SCHEMA, max_tokens=400)

    if result is None:
        # Fallback to single task
        return [{"start_minute": 0, "duration_minutes": duration_minutes, "subtask": activity}]

    return result.get("subtasks", [])


def decide_action(
    agent_context: AgentContext,
    available_actions: list[str],
) -> dict:
    """
    Let the agent decide what to do next from available options.

    Returns:
        {
            "chosen_action": "the action they chose",
            "reason": "why they chose it"
        }
    """
    system_prompt = """You are deciding what a person would do next based on their personality.
Choose from the available actions."""

    actions_text = "\n".join(f"- {a}" for a in available_actions)

    user_prompt = f"""Character: {agent_context.name}
Personality: {agent_context.personality_summary}
Current activity: {agent_context.current_activity}

Available actions:
{actions_text}

What would they choose and why?"""

    result = _call_llm(system_prompt, user_prompt, ACTION_SCHEMA, max_tokens=150)

    if result is None:
        return {
            "chosen_action": available_actions[0],
            "reason": "default choice"
        }

    return result


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("Cognition Module Test (Structured Outputs)\n")
    print("=" * 50)

    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY not set in .env file")
        print("Create a .env file with your API key:")
        print("  OPENROUTER_API_KEY=your_key_here")
        exit(1)

    # Create test context for Elena
    elena_context = AgentContext(
        name="Elena Rodriguez",
        age=34,
        occupation="Café Owner",
        bio="Runs a small café in the old town. Values community and local business.",
        personality_summary="extraverted, agreeable, open-minded",
        biases=["supports local business", "skeptical of big tech", "values personal relationships"],
        current_activity="working",
        current_location="café",
        relevant_memories=[
            "Signed up for NovaCRM to manage café customers",
            "Complained to Marco about rising software costs",
        ],
    )

    print("Testing reaction generation (structured output)...")
    print("-" * 50)

    reaction = generate_reaction(
        elena_context,
        "NovaCRM announces a 40% price increase effective next month"
    )

    print(f"Thought: {reaction['thought']}")
    print(f"Sentiment: {reaction['sentiment']}")
    print(f"Would share: {reaction['would_share']}")
    print(f"Share summary: {reaction['share_summary']}")

    print("\n" + "=" * 50)
    print("Testing thought generation...")
    print("-" * 50)

    thought = generate_thought(
        elena_context,
        "Morning rush just ended, café is quiet"
    )
    print(f"Elena thinks: {thought}")
