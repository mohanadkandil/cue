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
Keep it natural and brief (2-4 exchanges total). Match their personalities."""

    topic_text = f"They are discussing: {topic}" if topic else "They are having casual conversation."

    user_prompt = f"""Person 1: {agent1_context.name}, {agent1_context.age}, {agent1_context.occupation}
Personality: {agent1_context.personality_summary}
Currently: {agent1_context.current_activity}

Person 2: {agent2_context.name}, {agent2_context.age}, {agent2_context.occupation}
Personality: {agent2_context.personality_summary}
Currently: {agent2_context.current_activity}

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
