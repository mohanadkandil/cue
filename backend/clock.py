"""
Simulation Clock

Example: 1 real second = 5 simulation minutes
         So a full 24-hour sim day = ~5 real minutes
"""

from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class SimulationClock:
    """
    Tracks simulation time independent of real time.

    Attributes:
        current_time: The current datetime in simulation world
        tick_duration: How much sim time passes per tick (in minutes)
        start_time: When the simulation started (sim time)
    """
    current_time: datetime
    tick_duration: int = 5  # Each tick = 5 simulation minutes

    @classmethod
    def new(cls, start_hour: int = 6) -> "SimulationClock":
        """
        Create a new clock starting at a specific hour today.

        Args:
            start_hour: Hour to start simulation (default 6am)
        """
        today = datetime.now().replace(
            hour=start_hour,
            minute=0,
            second=0,
            microsecond=0
        )
        return cls(current_time=today)

    def tick(self) -> datetime:
        """
        Advance simulation time by one tick.
        Returns the new current time.
        """
        self.current_time += timedelta(minutes=self.tick_duration)
        return self.current_time

    @property
    def hour(self) -> int:
        """Current hour (0-23)"""
        return self.current_time.hour

    @property
    def minute(self) -> int:
        """Current minute (0-59)"""
        return self.current_time.minute

    @property
    def time_of_day(self) -> str:
        """Human readable time period"""
        hour = self.hour
        if 5 <= hour < 9:
            return "early_morning"
        elif 9 <= hour < 12:
            return "morning"
        elif 12 <= hour < 14:
            return "lunch"
        elif 14 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 20:
            return "evening"
        elif 20 <= hour < 23:
            return "night"
        else:
            return "late_night"

    @property
    def formatted_time(self) -> str:
        """Time as HH:MM string"""
        return self.current_time.strftime("%H:%M")

    @property
    def formatted_datetime(self) -> str:
        """Full datetime string"""
        return self.current_time.strftime("%A, %B %d, %H:%M")

    def is_between(self, start_hour: int, end_hour: int) -> bool:
        """Check if current time is between two hours"""
        return start_hour <= self.hour < end_hour


# Test when run directly
if __name__ == "__main__":
    # Create clock starting at 6am
    clock = SimulationClock.new(start_hour=6)

    print(f"Simulation started at: {clock.formatted_datetime}")
    print(f"Time of day: {clock.time_of_day}")
    print()

    # Simulate a few hours
    print("Advancing time...")
    for i in range(24):  # 24 ticks = 2 hours (at 5 min/tick)
        clock.tick()
        if i % 6 == 0:  # Print every 30 sim minutes
            print(f"  {clock.formatted_time} - {clock.time_of_day}")

    print()
    print(f"Final time: {clock.formatted_datetime}")
