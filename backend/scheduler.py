"""
Agent Scheduler

Defines daily routines for agents.
Given an agent and a time, returns what they should be doing.
"""

import random
from dataclasses import dataclass


@dataclass
class ScheduleBlock:
    """
    A block of time in an agent's schedule.

    Attributes:
        start_hour: When this block starts (0-23)
        end_hour: When this block ends (0-23)
        activity: What the agent is doing
        location: Where they are
        can_socialize: Whether they can chat with others
        can_be_interrupted: Whether events can reach them
    """
    start_hour: int
    end_hour: int
    activity: str
    location: str
    can_socialize: bool = True
    can_be_interrupted: bool = True

    def contains_hour(self, hour: int, offset: int = 0) -> bool:
        """Check if a given hour falls within this block (with optional offset)"""
        adjusted_start = (self.start_hour + offset) % 24
        adjusted_end = (self.end_hour + offset) % 24
        # Handle overnight blocks (e.g., 22:00 - 06:00)
        if adjusted_start > adjusted_end:
            return hour >= adjusted_start or hour < adjusted_end
        return adjusted_start <= hour < adjusted_end


# Pre-defined schedule templates based on occupation/lifestyle
SCHEDULE_TEMPLATES: dict[str, list[ScheduleBlock]] = {

    "cafe_owner": [
        ScheduleBlock(0, 6, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(6, 7, "morning routine", "home", can_socialize=False),
        ScheduleBlock(7, 8, "commuting", "transit", can_socialize=False),
        ScheduleBlock(8, 12, "working", "café", can_socialize=True),
        ScheduleBlock(12, 13, "lunch break", "café", can_socialize=True),
        ScheduleBlock(13, 18, "working", "café", can_socialize=True),
        ScheduleBlock(18, 19, "closing up", "café", can_socialize=True),
        ScheduleBlock(19, 21, "relaxing", "home", can_socialize=True),
        ScheduleBlock(21, 24, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
    ],

    "software_engineer": [
        ScheduleBlock(0, 7, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(7, 8, "morning routine", "home", can_socialize=False),
        ScheduleBlock(8, 9, "commuting", "transit", can_socialize=False),
        ScheduleBlock(9, 12, "working", "office", can_socialize=True),
        ScheduleBlock(12, 13, "lunch break", "office", can_socialize=True),
        ScheduleBlock(13, 18, "working", "office", can_socialize=True),
        ScheduleBlock(18, 19, "commuting", "transit", can_socialize=False),
        ScheduleBlock(19, 22, "relaxing", "home", can_socialize=True),
        ScheduleBlock(22, 24, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
    ],

    "freelancer": [
        ScheduleBlock(0, 8, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(8, 9, "morning routine", "home", can_socialize=False),
        ScheduleBlock(9, 12, "working", "home", can_socialize=True),
        ScheduleBlock(12, 13, "lunch break", "home", can_socialize=True),
        ScheduleBlock(13, 17, "working", "home", can_socialize=True),
        ScheduleBlock(17, 18, "exercise", "outside", can_socialize=False),
        ScheduleBlock(18, 22, "relaxing", "home", can_socialize=True),
        ScheduleBlock(22, 24, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
    ],

    "student": [
        ScheduleBlock(0, 8, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(8, 9, "morning routine", "home", can_socialize=False),
        ScheduleBlock(9, 12, "attending class", "university", can_socialize=False),
        ScheduleBlock(12, 13, "lunch break", "university", can_socialize=True),
        ScheduleBlock(13, 16, "studying", "library", can_socialize=False),
        ScheduleBlock(16, 18, "free time", "campus", can_socialize=True),
        ScheduleBlock(18, 20, "studying", "home", can_socialize=True),
        ScheduleBlock(20, 23, "relaxing", "home", can_socialize=True),
        ScheduleBlock(23, 24, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
    ],

    "executive": [
        ScheduleBlock(0, 6, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(6, 7, "morning routine", "home", can_socialize=False),
        ScheduleBlock(7, 8, "commuting", "transit", can_socialize=False),
        ScheduleBlock(8, 12, "meetings", "office", can_socialize=True),
        ScheduleBlock(12, 13, "business lunch", "restaurant", can_socialize=True),
        ScheduleBlock(13, 18, "meetings", "office", can_socialize=True),
        ScheduleBlock(18, 19, "commuting", "transit", can_socialize=False),
        ScheduleBlock(19, 21, "networking event", "venue", can_socialize=True),
        ScheduleBlock(21, 24, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
    ],

    "retired": [
        ScheduleBlock(0, 7, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(7, 9, "morning routine", "home", can_socialize=False),
        ScheduleBlock(9, 11, "reading news", "home", can_socialize=True),
        ScheduleBlock(11, 12, "walking", "park", can_socialize=True),
        ScheduleBlock(12, 14, "lunch", "home", can_socialize=True),
        ScheduleBlock(14, 17, "hobbies", "home", can_socialize=True),
        ScheduleBlock(17, 19, "socializing", "café", can_socialize=True),
        ScheduleBlock(19, 21, "dinner", "home", can_socialize=True),
        ScheduleBlock(21, 24, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
    ],

    # Default for anyone not matching above
    "default": [
        ScheduleBlock(0, 7, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(7, 8, "morning routine", "home", can_socialize=False),
        ScheduleBlock(8, 12, "working", "workplace", can_socialize=True),
        ScheduleBlock(12, 13, "lunch break", "workplace", can_socialize=True),
        ScheduleBlock(13, 17, "working", "workplace", can_socialize=True),
        ScheduleBlock(17, 19, "free time", "various", can_socialize=True),
        ScheduleBlock(19, 22, "relaxing", "home", can_socialize=True),
        ScheduleBlock(22, 24, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
    ],

    # Early bird variant
    "early_bird": [
        ScheduleBlock(0, 5, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(5, 6, "morning workout", "gym", can_socialize=True),
        ScheduleBlock(6, 7, "morning routine", "home", can_socialize=False),
        ScheduleBlock(7, 11, "deep work", "office", can_socialize=True),
        ScheduleBlock(11, 12, "lunch break", "cafe", can_socialize=True),
        ScheduleBlock(12, 16, "meetings", "office", can_socialize=True),
        ScheduleBlock(16, 18, "networking", "coworking space", can_socialize=True),
        ScheduleBlock(18, 21, "relaxing", "home", can_socialize=True),
        ScheduleBlock(21, 24, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
    ],

    # Night owl variant
    "night_owl": [
        ScheduleBlock(0, 2, "side projects", "home", can_socialize=True),
        ScheduleBlock(2, 9, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(9, 10, "morning routine", "home", can_socialize=False),
        ScheduleBlock(10, 11, "coffee", "cafe", can_socialize=True),
        ScheduleBlock(11, 14, "working", "coworking space", can_socialize=True),
        ScheduleBlock(14, 15, "lunch break", "restaurant", can_socialize=True),
        ScheduleBlock(15, 19, "working", "coworking space", can_socialize=True),
        ScheduleBlock(19, 21, "dinner", "restaurant", can_socialize=True),
        ScheduleBlock(21, 24, "socializing", "bar", can_socialize=True),
    ],

    # Social butterfly
    "social": [
        ScheduleBlock(0, 7, "sleeping", "home", can_socialize=False, can_be_interrupted=False),
        ScheduleBlock(7, 8, "morning routine", "home", can_socialize=False),
        ScheduleBlock(8, 10, "coffee meetings", "cafe", can_socialize=True),
        ScheduleBlock(10, 12, "working", "office", can_socialize=True),
        ScheduleBlock(12, 14, "lunch networking", "restaurant", can_socialize=True),
        ScheduleBlock(14, 17, "meetings", "various", can_socialize=True),
        ScheduleBlock(17, 19, "happy hour", "bar", can_socialize=True),
        ScheduleBlock(19, 21, "dinner event", "venue", can_socialize=True),
        ScheduleBlock(21, 24, "relaxing", "home", can_socialize=True),
    ],
}


# Map agent occupations to schedule templates
OCCUPATION_TO_TEMPLATE: dict[str, str] = {
    "Café Owner": "cafe_owner",
    "Restaurant Owner": "cafe_owner",
    "Software Engineer": "software_engineer",
    "Engineering Manager": "software_engineer",
    "Junior Developer": "software_engineer",
    "Freelance Developer": "freelancer",
    "UX Designer": "software_engineer",
    "Content Creator": "freelancer",
    "Graduate Student": "student",
    "Intern": "student",
    "Apprentice": "student",
    "CTO": "executive",
    "IT Director": "executive",
    "Marketing Director": "executive",
    "Board Advisor": "retired",
    "University Professor": "software_engineer",
    "Research Scientist": "software_engineer",
    # Luma / Events personas
    "Event Organizer": "executive",
    "Community Manager": "freelancer",
    "Founder": "executive",
    "VC Partner": "executive",
    "Investor": "executive",
    "Developer Relations": "software_engineer",
    "Head of Community": "executive",
    "Growth Lead": "executive",
    "Product Manager": "software_engineer",
    "Startup Founder": "executive",
    "Angel Investor": "executive",
    "Conference Organizer": "executive",
    "Tech Evangelist": "freelancer",
    "Community Lead": "freelancer",
}


def get_schedule_for_occupation(occupation: str) -> list[ScheduleBlock]:
    """Get the schedule template for an occupation"""
    template_name = OCCUPATION_TO_TEMPLATE.get(occupation, "default")
    return SCHEDULE_TEMPLATES[template_name]


# Cache agent schedule variants and offsets for consistency
_agent_variants: dict[str, str] = {}
_agent_offsets: dict[str, int] = {}

def get_agent_variant(agent_id: str, base_template: str) -> str:
    """Get a consistent schedule variant for an agent"""
    if agent_id not in _agent_variants:
        random.seed(hash(agent_id + "variant"))
        # 40% use base template, 60% get a variant
        roll = random.random()
        if roll < 0.4:
            _agent_variants[agent_id] = base_template
        elif roll < 0.55:
            _agent_variants[agent_id] = "early_bird"
        elif roll < 0.70:
            _agent_variants[agent_id] = "night_owl"
        elif roll < 0.85:
            _agent_variants[agent_id] = "social"
        else:
            _agent_variants[agent_id] = base_template
        random.seed()
    return _agent_variants[agent_id]

def get_agent_offset(agent_id: str) -> int:
    """Get a consistent random offset for an agent (-1 to 2 hours)"""
    if agent_id not in _agent_offsets:
        random.seed(hash(agent_id + "offset"))
        _agent_offsets[agent_id] = random.randint(-1, 2)
        random.seed()
    return _agent_offsets[agent_id]


def get_current_activity(occupation: str, hour: int, agent_id: str = None) -> ScheduleBlock:
    """
    Get what an agent should be doing at a given hour.

    Args:
        occupation: The agent's occupation
        hour: Current hour (0-23)
        agent_id: Optional agent ID for schedule variance

    Returns:
        The ScheduleBlock for this time
    """
    # Get base template for occupation
    base_template = OCCUPATION_TO_TEMPLATE.get(occupation, "default")

    # Maybe use a variant based on agent personality
    if agent_id:
        template_name = get_agent_variant(agent_id, base_template)
    else:
        template_name = base_template

    schedule = SCHEDULE_TEMPLATES.get(template_name, SCHEDULE_TEMPLATES["default"])

    # Apply per-agent time offset for variety
    offset = get_agent_offset(agent_id) if agent_id else 0
    adjusted_hour = (hour - offset) % 24

    for block in schedule:
        if block.contains_hour(adjusted_hour):
            return block

    # Fallback (should never happen if schedules cover 24h)
    return ScheduleBlock(0, 24, "unknown", "unknown")


def get_agents_who_can_socialize(agents: list, hour: int) -> list:
    """
    Filter agents to only those who can socialize at this hour.

    Args:
        agents: List of Agent objects
        hour: Current hour

    Returns:
        Agents whose current activity allows socializing
    """
    available = []
    for agent in agents:
        block = get_current_activity(agent.occupation, hour)
        if block.can_socialize:
            available.append(agent)
    return available


# Test when run directly
if __name__ == "__main__":
    print("Schedule Templates Demo\n")

    # Show Elena's day (café owner)
    print("Elena (Café Owner) - Full Day:")
    print("-" * 50)
    for hour in range(24):
        block = get_current_activity("Café Owner", hour)
        status = "💬" if block.can_socialize else "🔇"
        print(f"  {hour:02d}:00 - {block.activity:<20} @ {block.location:<10} {status}")

    print("\n")

    # Show a specific time check
    print("At 10:00 AM:")
    for occupation in ["Café Owner", "Software Engineer", "Graduate Student"]:
        block = get_current_activity(occupation, 10)
        print(f"  {occupation}: {block.activity} @ {block.location}")
