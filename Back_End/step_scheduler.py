"""
Step Scheduler for Multi-Step Missions

Per-step scheduling engine with:
- Time-based scheduling: "Every Monday 9am", "Tomorrow 3pm"
- Event-based scheduling: "After step 3 completes", "When email arrives"
- Recurring schedules: "Daily", "Weekly", "Monthly"
- Cascade scheduling: "Chain step 1 → 2 → 3"

Philosophy:
- Schedule PER-STEP (not per-mission)
- Clear trigger conditions
- Firebase persistence
- User-friendly format

Author: Buddy Phase 2 Architecture Team
Date: February 11, 2026
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ScheduleTrigger(Enum):
    """Schedule trigger types"""
    TIME_BASED = "time"  # Specific date/time
    EVENT_BASED = "event"  # After another step completes
    RECURRING = "recurring"  # Repeating pattern
    CASCADE = "cascade"  # Chain of steps
    IMMEDIATE = "immediate"  # Execute now


class RecurrencePattern(Enum):
    """Recurrence patterns"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class StepSchedule:
    """
    Schedule configuration for a single step.
    
    Examples:
    - Time-based: trigger=TIME_BASED, scheduled_time="2026-02-15T09:00:00Z"
    - Event-based: trigger=EVENT_BASED, depends_on_step=2, event_condition="success"
    - Recurring: trigger=RECURRING, recurrence="daily", scheduled_time="09:00:00"
    - Cascade: trigger=CASCADE, depends_on_step=1 (runs after previous step)
    - Immediate: trigger=IMMEDIATE (runs now)
    """
    step_number: int
    trigger: ScheduleTrigger
    
    # Time-based scheduling
    scheduled_time: Optional[str] = None  # ISO 8601 format
    
    # Event-based scheduling
    depends_on_step: Optional[int] = None  # Step number to wait for
    event_condition: str = "success"  # success, failure, complete, custom_event
    
    # Recurring scheduling
    recurrence: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[str] = None
    
    # Cascade scheduling (implicit dependency on previous step)
    cascade_delay_seconds: int = 0  # Delay after dependency completes
    
    # Metadata
    description: str = ""
    timezone: str = "UTC"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'step_number': self.step_number,
            'trigger': self.trigger.value,
            'scheduled_time': self.scheduled_time,
            'depends_on_step': self.depends_on_step,
            'event_condition': self.event_condition,
            'recurrence': self.recurrence.value if self.recurrence else None,
            'recurrence_end_date': self.recurrence_end_date,
            'cascade_delay_seconds': self.cascade_delay_seconds,
            'description': self.description,
            'timezone': self.timezone
        }
    
    def to_human_readable(self) -> str:
        """Generate human-readable schedule description"""
        if self.trigger == ScheduleTrigger.IMMEDIATE:
            return "Execute immediately"
        
        elif self.trigger == ScheduleTrigger.TIME_BASED:
            if self.scheduled_time:
                # Parse ISO timestamp and format nicely
                try:
                    dt = datetime.fromisoformat(self.scheduled_time.replace('Z', '+00:00'))
                    return f"Scheduled for {dt.strftime('%B %d, %Y at %I:%M %p %Z')}"
                except:
                    return f"Scheduled for {self.scheduled_time}"
            return "Time-based schedule (time not specified)"
        
        elif self.trigger == ScheduleTrigger.EVENT_BASED:
            if self.depends_on_step:
                condition_text = {
                    'success': 'succeeds',
                    'failure': 'fails',
                    'complete': 'completes'
                }.get(self.event_condition, self.event_condition)
                return f"After step {self.depends_on_step} {condition_text}"
            return "Event-based schedule"
        
        elif self.trigger == ScheduleTrigger.RECURRING:
            if self.recurrence:
                pattern_text = self.recurrence.value.capitalize()
                if self.scheduled_time:
                    try:
                        # Parse time component
                        time_str = self.scheduled_time.split('T')[1] if 'T' in self.scheduled_time else self.scheduled_time
                        hour, minute = time_str.split(':')[:2]
                        return f"{pattern_text} at {int(hour):02d}:{int(minute):02d}"
                    except:
                        return f"{pattern_text}"
                return f"{pattern_text} recurrence"
            return "Recurring schedule"
        
        elif self.trigger == ScheduleTrigger.CASCADE:
            if self.depends_on_step:
                if self.cascade_delay_seconds > 0:
                    return f"After step {self.depends_on_step} (+ {self.cascade_delay_seconds}s delay)"
                return f"Immediately after step {self.depends_on_step}"
            return "Cascade schedule"
        
        return "Unscheduled"


class StepScheduler:
    """
    Manages scheduling for multi-step missions.
    
    Features:
    - Create schedules for steps
    - Validate schedule dependencies
    - Generate human-readable descriptions
    - Detect parallelization opportunities
    """
    
    def __init__(self):
        logger.info("StepScheduler initialized")
    
    def create_immediate_schedule(self, step_number: int) -> StepSchedule:
        """Create immediate execution schedule"""
        return StepSchedule(
            step_number=step_number,
            trigger=ScheduleTrigger.IMMEDIATE,
            description="Execute immediately"
        )
    
    def create_time_schedule(
        self,
        step_number: int,
        scheduled_time: str,
        timezone: str = "UTC"
    ) -> StepSchedule:
        """
        Create time-based schedule.
        
        Args:
            step_number: Step number
            scheduled_time: ISO 8601 format (e.g., "2026-02-15T09:00:00Z")
            timezone: Timezone (default: UTC)
            
        Returns:
            StepSchedule configured for time-based execution
        """
        return StepSchedule(
            step_number=step_number,
            trigger=ScheduleTrigger.TIME_BASED,
            scheduled_time=scheduled_time,
            timezone=timezone,
            description=f"Scheduled for {scheduled_time}"
        )
    
    def create_event_schedule(
        self,
        step_number: int,
        depends_on_step: int,
        event_condition: str = "success"
    ) -> StepSchedule:
        """
        Create event-based schedule.
        
        Args:
            step_number: Step number
            depends_on_step: Step number to wait for
            event_condition: Condition to trigger (success, failure, complete)
            
        Returns:
            StepSchedule configured for event-based execution
        """
        return StepSchedule(
            step_number=step_number,
            trigger=ScheduleTrigger.EVENT_BASED,
            depends_on_step=depends_on_step,
            event_condition=event_condition,
            description=f"After step {depends_on_step} {event_condition}"
        )
    
    def create_recurring_schedule(
        self,
        step_number: int,
        recurrence: RecurrencePattern,
        scheduled_time: str,  # Time of day (e.g., "09:00:00")
        end_date: Optional[str] = None,
        timezone: str = "UTC"
    ) -> StepSchedule:
        """
        Create recurring schedule.
        
        Args:
            step_number: Step number
            recurrence: Recurrence pattern (daily, weekly, etc.)
            scheduled_time: Time of day to execute
            end_date: Optional end date for recurrence
            timezone: Timezone (default: UTC)
            
        Returns:
            StepSchedule configured for recurring execution
        """
        return StepSchedule(
            step_number=step_number,
            trigger=ScheduleTrigger.RECURRING,
            recurrence=recurrence,
            scheduled_time=scheduled_time,
            recurrence_end_date=end_date,
            timezone=timezone,
            description=f"{recurrence.value.capitalize()} at {scheduled_time}"
        )
    
    def create_cascade_schedule(
        self,
        step_number: int,
        depends_on_step: int,
        delay_seconds: int = 0
    ) -> StepSchedule:
        """
        Create cascade schedule (chain execution).
        
        Args:
            step_number: Step number
            depends_on_step: Previous step in chain
            delay_seconds: Optional delay after dependency completes
            
        Returns:
            StepSchedule configured for cascade execution
        """
        return StepSchedule(
            step_number=step_number,
            trigger=ScheduleTrigger.CASCADE,
            depends_on_step=depends_on_step,
            cascade_delay_seconds=delay_seconds,
            description=f"Chain: after step {depends_on_step}"
        )
    
    def auto_schedule_steps(
        self,
        num_steps: int,
        default_trigger: ScheduleTrigger = ScheduleTrigger.CASCADE
    ) -> List[StepSchedule]:
        """
        Auto-generate schedules for steps.
        
        Default behavior: Cascade (step 1 → step 2 → step 3...)
        
        Args:
            num_steps: Number of steps
            default_trigger: Default trigger type
            
        Returns:
            List of StepSchedule objects
        """
        schedules = []
        
        for step_num in range(1, num_steps + 1):
            if step_num == 1:
                # First step: immediate
                schedule = self.create_immediate_schedule(step_num)
            else:
                # Subsequent steps: cascade from previous
                if default_trigger == ScheduleTrigger.CASCADE:
                    schedule = self.create_cascade_schedule(
                        step_number=step_num,
                        depends_on_step=step_num - 1
                    )
                else:
                    # Default to immediate if not cascade
                    schedule = self.create_immediate_schedule(step_num)
            
            schedules.append(schedule)
        
        return schedules
    
    def validate_schedules(
        self,
        schedules: List[StepSchedule]
    ) -> List[Dict[str, Any]]:
        """
        Validate schedule configurations.
        
        Checks:
        - Dependency cycles
        - Invalid step references
        - Missing required fields
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        step_numbers = {s.step_number for s in schedules}
        
        for schedule in schedules:
            # Check dependency references
            if schedule.depends_on_step and schedule.depends_on_step not in step_numbers:
                issues.append({
                    'step': schedule.step_number,
                    'issue': 'invalid_dependency',
                    'message': f"Step {schedule.step_number} depends on non-existent step {schedule.depends_on_step}"
                })
            
            # Check time-based schedules have time
            if schedule.trigger == ScheduleTrigger.TIME_BASED and not schedule.scheduled_time:
                issues.append({
                    'step': schedule.step_number,
                    'issue': 'missing_time',
                    'message': f"Step {schedule.step_number} has time-based trigger but no scheduled_time"
                })
            
            # Check recurring schedules have pattern
            if schedule.trigger == ScheduleTrigger.RECURRING:
                if not schedule.recurrence:
                    issues.append({
                        'step': schedule.step_number,
                        'issue': 'missing_recurrence',
                        'message': f"Step {schedule.step_number} has recurring trigger but no recurrence pattern"
                    })
                if not schedule.scheduled_time:
                    issues.append({
                        'step': schedule.step_number,
                        'issue': 'missing_time',
                        'message': f"Step {schedule.step_number} has recurring trigger but no scheduled_time"
                    })
        
        # Check for dependency cycles
        visited = set()
        recursion_stack = set()
        
        def has_cycle(step_num: int) -> bool:
            if step_num in recursion_stack:
                return True
            if step_num in visited:
                return False
            
            visited.add(step_num)
            recursion_stack.add(step_num)
            
            # Find schedule for this step
            schedule = next((s for s in schedules if s.step_number == step_num), None)
            if schedule and schedule.depends_on_step:
                if has_cycle(schedule.depends_on_step):
                    return True
            
            recursion_stack.remove(step_num)
            return False
        
        for schedule in schedules:
            if has_cycle(schedule.step_number):
                issues.append({
                    'step': schedule.step_number,
                    'issue': 'dependency_cycle',
                    'message': f"Step {schedule.step_number} is part of a dependency cycle"
                })
                break
        
        return issues
    
    def detect_parallel_steps(
        self,
        schedules: List[StepSchedule]
    ) -> List[List[int]]:
        """
        Detect steps that can run in parallel.
        
        Steps can run in parallel if:
        - They don't depend on each other (directly or transitively)
        - They have IMMEDIATE trigger or same scheduled_time
        
        Returns:
            List of parallel step groups (e.g., [[1, 2], [3, 4]])
        """
        parallel_groups = []
        
        # Group by trigger type and dependencies
        immediate_steps = [
            s for s in schedules
            if s.trigger == ScheduleTrigger.IMMEDIATE
        ]
        
        # Check for independent immediate steps
        if len(immediate_steps) > 1:
            independent = []
            for step in immediate_steps:
                # Check if step has no dependencies
                if not step.depends_on_step:
                    independent.append(step.step_number)
            
            if len(independent) > 1:
                parallel_groups.append(independent)
        
        return parallel_groups


# Singleton instance
step_scheduler = StepScheduler()
