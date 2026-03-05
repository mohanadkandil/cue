"""
Agent Scheduler

Defines daily routines for agents.
Given an agent and a time, returns what they should be doing.
"""

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

    def contains_hour(self, hour: int) -> bool:
        """Check if a given hour falls within this block"""
        # Handle overnight blocks (e.g., 22:00 - 06:00)
        if self.start_hour > self.end_hour:
            return hour >= self.start_hour or hour < self.end_hour
        return self.start_hour <= hour < self.end_hour


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
}


def get_schedule_for_occupation(occupation: str) -> list[ScheduleBlock]:
    """Get the schedule template for an occupation"""
    template_name = OCCUPATION_TO_TEMPLATE.get(occupation, "default")
    return SCHEDULE_TEMPLATES[template_name]


def get_current_activity(occupation: str, hour: int) -> ScheduleBlock:
    """
    Get what an agent should be doing at a given hour.

    Args:
        occupation: The agent's occupation
        hour: Current hour (0-23)

    Returns:
        The ScheduleBlock for this time
    """
    schedule = get_schedule_for_occupation(occupation)

    for block in schedule:
        if block.contains_hour(hour):
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
