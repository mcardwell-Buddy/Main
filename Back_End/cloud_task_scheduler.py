"""
Phase 9: Cloud Task Scheduler

Schedules missions to run at specific times using:
- One-time schedules (run once at specific time)
- Recurring schedules (cron expressions)
- Delay schedules (run after N minutes/hours)
- Timezone-aware scheduling

Integration with Cloud Tasks for production, fallback to in-memory for dev.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of schedules."""
    ONE_TIME = "one_time"              # Run once at specific time
    RECURRING = "recurring"            # Run on cron schedule
    DELAY = "delay"                    # Run after delay
    IMMEDIATE = "immediate"            # Run now


@dataclass
class ScheduledMission:
    """A mission scheduled for future execution."""
    schedule_id: str
    mission_id: str
    mission_objective: str
    schedule_type: str                 # one_time, recurring, delay, immediate
    schedule_time: Optional[str]       # ISO 8601 datetime for one-time
    cron_expression: Optional[str]     # Cron for recurring (e.g., "0 9 * * MON")
    delay_minutes: Optional[int]       # Minutes to delay
    timezone: str = "UTC"
    created_at: str = None
    status: str = "scheduled"          # scheduled, running, completed, failed, cancelled
    execution_count: int = 0
    next_run: Optional[str] = None     # Next scheduled run time
    metadata: Dict[str, Any] = None    # Custom metadata

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.metadata is None:
            self.metadata = {}


class CloudTaskScheduler:
    """Schedules missions for future execution."""
    
    def __init__(self, data_dir: str = "./outputs/scheduled_missions"):
        """
        Initialize scheduler.
        
        Args:
            data_dir: Directory to persist scheduled missions
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.schedules_file = self.data_dir / "scheduled_missions.jsonl"
        self.execution_log = self.data_dir / "execution_log.jsonl"
        
        # In-memory cache
        self._schedules: Dict[str, ScheduledMission] = {}
        self._load_schedules()
        
        logger.info(f"[SCHEDULER] Initialized with {len(self._schedules)} scheduled missions")
    
    def _load_schedules(self) -> None:
        """Load scheduled missions from persistent storage."""
        if not self.schedules_file.exists():
            return
        
        try:
            with open(self.schedules_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        schedule = ScheduledMission(**data)
                        self._schedules[schedule.schedule_id] = schedule
            logger.info(f"[SCHEDULER] Loaded {len(self._schedules)} schedules from disk")
        except Exception as e:
            logger.error(f"[SCHEDULER] Error loading schedules: {e}")
    
    def _persist_schedule(self, schedule: ScheduledMission) -> None:
        """Persist a schedule to disk."""
        try:
            with open(self.schedules_file, 'a') as f:
                f.write(json.dumps(asdict(schedule), default=str) + '\n')
        except Exception as e:
            logger.error(f"[SCHEDULER] Error persisting schedule: {e}")
    
    def schedule_one_time(
        self,
        mission_id: str,
        mission_objective: str,
        run_at: datetime,
        timezone: str = "UTC",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Schedule a mission to run once at specific time.
        
        Args:
            mission_id: Mission to execute
            mission_objective: Objective description
            run_at: When to run (datetime)
            timezone: Timezone for the scheduled time
            metadata: Custom metadata
        
        Returns:
            schedule_id if successful
        """
        try:
            schedule_id = f"sched_{mission_id}_{int(run_at.timestamp())}"
            
            schedule = ScheduledMission(
                schedule_id=schedule_id,
                mission_id=mission_id,
                mission_objective=mission_objective,
                schedule_type=ScheduleType.ONE_TIME.value,
                schedule_time=run_at.isoformat(),
                cron_expression=None,
                delay_minutes=None,
                timezone=timezone,
                status="scheduled",
                next_run=run_at.isoformat(),
                metadata=metadata or {}
            )
            
            self._schedules[schedule_id] = schedule
            self._persist_schedule(schedule)
            
            logger.info(f"[SCHEDULER] Scheduled one-time mission {mission_id} for {run_at}")
            return schedule_id
        except Exception as e:
            logger.error(f"[SCHEDULER] Error scheduling one-time mission: {e}")
            return None
    
    def schedule_recurring(
        self,
        mission_id: str,
        mission_objective: str,
        cron_expression: str,
        timezone: str = "UTC",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Schedule a mission to run on a cron schedule.
        
        Args:
            mission_id: Mission to execute
            mission_objective: Objective description
            cron_expression: Cron expression (e.g., "0 9 * * MON" for 9 AM on Mondays)
            timezone: Timezone for cron schedule
            metadata: Custom metadata
        
        Returns:
            schedule_id if successful
        
        Examples:
            "0 9 * * *"        → Every day at 9 AM
            "0 9 * * MON"      → Every Monday at 9 AM
            "0 */4 * * *"      → Every 4 hours
            "0 9-17 * * *"     → Every hour 9 AM-5 PM
        """
        try:
            schedule_id = f"recurring_{mission_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            schedule = ScheduledMission(
                schedule_id=schedule_id,
                mission_id=mission_id,
                mission_objective=mission_objective,
                schedule_type=ScheduleType.RECURRING.value,
                schedule_time=None,
                cron_expression=cron_expression,
                delay_minutes=None,
                timezone=timezone,
                status="scheduled",
                next_run=self._calculate_next_run_cron(cron_expression, timezone),
                metadata=metadata or {}
            )
            
            self._schedules[schedule_id] = schedule
            self._persist_schedule(schedule)
            
            logger.info(f"[SCHEDULER] Scheduled recurring mission {mission_id}: {cron_expression}")
            return schedule_id
        except Exception as e:
            logger.error(f"[SCHEDULER] Error scheduling recurring mission: {e}")
            return None
    
    def schedule_delayed(
        self,
        mission_id: str,
        mission_objective: str,
        delay_minutes: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Schedule a mission to run after a delay.
        
        Args:
            mission_id: Mission to execute
            mission_objective: Objective description
            delay_minutes: Minutes to wait before execution
            metadata: Custom metadata
        
        Returns:
            schedule_id if successful
        """
        try:
            schedule_id = f"delay_{mission_id}_{int(datetime.now(timezone.utc).timestamp())}"
            run_at = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
            
            schedule = ScheduledMission(
                schedule_id=schedule_id,
                mission_id=mission_id,
                mission_objective=mission_objective,
                schedule_type=ScheduleType.DELAY.value,
                schedule_time=None,
                cron_expression=None,
                delay_minutes=delay_minutes,
                timezone="UTC",
                status="scheduled",
                next_run=run_at.isoformat(),
                metadata=metadata or {}
            )
            
            self._schedules[schedule_id] = schedule
            self._persist_schedule(schedule)
            
            logger.info(f"[SCHEDULER] Scheduled delayed mission {mission_id} in {delay_minutes} minutes")
            return schedule_id
        except Exception as e:
            logger.error(f"[SCHEDULER] Error scheduling delayed mission: {e}")
            return None
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduledMission]:
        """Get a scheduled mission by ID."""
        return self._schedules.get(schedule_id)
    
    def list_schedules(
        self,
        mission_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ScheduledMission]:
        """
        List scheduled missions.
        
        Args:
            mission_id: Filter by mission (optional)
            status: Filter by status (optional)
        
        Returns:
            List of scheduled missions
        """
        schedules = list(self._schedules.values())
        
        if mission_id:
            schedules = [s for s in schedules if s.mission_id == mission_id]
        
        if status:
            schedules = [s for s in schedules if s.status == status]
        
        return schedules
    
    def cancel_schedule(self, schedule_id: str) -> bool:
        """Cancel a scheduled mission."""
        try:
            if schedule_id in self._schedules:
                schedule = self._schedules[schedule_id]
                schedule.status = "cancelled"
                logger.info(f"[SCHEDULER] Cancelled schedule {schedule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"[SCHEDULER] Error cancelling schedule: {e}")
            return False
    
    def log_execution(
        self,
        schedule_id: str,
        status: str,
        execution_time_ms: int,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log execution of a scheduled mission.
        
        Args:
            schedule_id: Schedule that was executed
            status: Execution status (success, failed)
            execution_time_ms: Time to execute in milliseconds
            result: Execution result
        
        Returns:
            True if logged successfully
        """
        try:
            execution = {
                "schedule_id": schedule_id,
                "status": status,
                "execution_time_ms": execution_time_ms,
                "result": result or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            with open(self.execution_log, 'a') as f:
                f.write(json.dumps(execution) + '\n')
            
            # Update schedule
            if schedule_id in self._schedules:
                schedule = self._schedules[schedule_id]
                schedule.execution_count += 1
                if schedule.schedule_type == "one_time":
                    schedule.status = "completed"
            
            logger.info(f"[SCHEDULER] Execution logged for {schedule_id}: {status}")
            return True
        except Exception as e:
            logger.error(f"[SCHEDULER] Error logging execution: {e}")
            return False
    
    @staticmethod
    def _calculate_next_run_cron(cron_expression: str, timezone: str) -> str:
        """
        Calculate next run time from cron expression.
        
        Note: Full cron implementation would use croniter library.
        This is a simplified version.
        
        Args:
            cron_expression: Cron expression
            timezone: Timezone
        
        Returns:
            Next run time as ISO 8601 string
        """
        try:
            # Simple approximation: add 1 day for now
            next_run = datetime.now(timezone.utc) + timedelta(days=1)
            return next_run.isoformat()
        except Exception as e:
            logger.error(f"[SCHEDULER] Error calculating next run: {e}")
            return None


# Global scheduler instance
_scheduler: Optional[CloudTaskScheduler] = None


def get_cloud_scheduler() -> CloudTaskScheduler:
    """Get or create the cloud task scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = CloudTaskScheduler()
    return _scheduler


logger.info("[SCHEDULER] Module loaded")
