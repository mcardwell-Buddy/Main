"""
Mission Executor - Minimal async execution of queued missions.

Flow:
1. Dequeue mission from execution_queue
2. Call execute_goal() with mission objective
3. Capture result
4. Write mission status update to missions.jsonl
5. Emit signal to learning_signals.jsonl

NO retries, NO looping, ONE execution per mission.
"""

import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from collections import deque

logger = logging.getLogger(__name__)


class ExecutionQueue:
    """Simple in-memory queue for missions."""
    
    def __init__(self):
        self._queue = deque()
        self._queued = set()  # Track mission_ids currently in queue
    
    def enqueue(self, mission_data: Dict[str, Any]) -> None:
        """Enqueue a mission for execution."""
        mission_id = mission_data.get('mission_id')
        if mission_id and mission_id not in self._queued:
            self._queue.append(mission_data)
            self._queued.add(mission_id)
            logger.info(f"[EXECUTOR] Queued mission: {mission_id}")
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Dequeue next mission. Returns None if queue empty."""
        try:
            mission_data = self._queue.popleft()
            mission_id = mission_data.get('mission_id')
            if mission_id and mission_id in self._queued:
                self._queued.discard(mission_id)
            return mission_data
        except IndexError:
            return None
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._queue) == 0
    
    def size(self) -> int:
        """Return queue size."""
        return len(self._queue)


# Global execution queue (singleton)
execution_queue = ExecutionQueue()


class MissionExecutor:
    """Executes queued missions."""
    
    def __init__(
        self,
        missions_file: str = 'outputs/phase25/missions.jsonl',
        signals_file: str = 'outputs/phase25/learning_signals.jsonl'
    ):
        self.missions_file = Path(missions_file)
        self.signals_file = Path(signals_file)
        self.running = False
        
        # Ensure output directories exist
        self.missions_file.parent.mkdir(parents=True, exist_ok=True)
        self.signals_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def execute_mission(self, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single mission.
        
        Args:
            mission_data: {mission_id, objective, constraints, ...}
            
        Returns:
            {success, mission_id, result, error}
        """
        mission_id = mission_data.get('mission_id')
        objective = mission_data.get('objective', {})
        
        logger.info(f"[EXECUTOR] Starting execution of mission {mission_id}")
        
        try:
            # Update mission status to "active"
            self._write_mission_update(
                mission_id=mission_id,
                status='active',
                reason='execution_started'
            )
            
            # Execute the goal (synchronous function in async context)
            from Back_End.composite_agent import execute_goal
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                execute_goal,
                objective.get('description', ''),
                objective.get('type', '_global')
            )
            
            # Write execution result to mission
            success = result.get('success', False)
            final_status = 'completed' if success else 'failed'
            
            self._write_mission_update(
                mission_id=mission_id,
                status=final_status,
                reason='execution_finished',
                result=result
            )
            
            # Emit signal
            self._emit_execution_signal(
                mission_id=mission_id,
                status=final_status,
                result=result
            )
            
            logger.info(f"[EXECUTOR] Mission {mission_id} {final_status}")
            
            return {
                'success': True,
                'mission_id': mission_id,
                'status': final_status,
                'result': result
            }
        
        except Exception as e:
            logger.error(f"[EXECUTOR] Error executing mission {mission_id}: {e}", exc_info=True)
            
            # Write failure
            self._write_mission_update(
                mission_id=mission_id,
                status='failed',
                reason='execution_error',
                error=str(e)
            )
            
            # Emit failure signal
            self._emit_execution_signal(
                mission_id=mission_id,
                status='failed',
                error=str(e)
            )
            
            return {
                'success': False,
                'mission_id': mission_id,
                'status': 'failed',
                'error': str(e)
            }
    
    def _write_mission_update(
        self,
        mission_id: str,
        status: str,
        reason: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Write mission status update to missions.jsonl (append-only).
        """
        try:
            update_record = {
                'event_type': 'mission_status_update',
                'mission_id': mission_id,
                'status': status,
                'reason': reason,
                'completed_at': datetime.now(timezone.utc).isoformat() if status in ['completed', 'failed'] else None,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            
            if result:
                # Include steps and other execution details for debugging/analysis
                update_record['execution_result'] = {
                    'final_answer': result.get('final_answer'),
                    'success': result.get('success'),
                    'tools_used': result.get('tools_used', []),
                    'steps': result.get('steps', []),  # Include full step trace
                    'total_steps': result.get('total_steps', len(result.get('steps', []))),
                }
            
            if error:
                update_record['error'] = error
            
            # Append to missions.jsonl
            with open(self.missions_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(update_record) + '\n')
            
            logger.info(f"[EXECUTOR] Wrote mission update: {mission_id} → {status}")
        
        except Exception as e:
            logger.error(f"[EXECUTOR] Error writing mission update: {e}", exc_info=True)
    
    def _emit_execution_signal(
        self,
        mission_id: str,
        status: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Emit execution signal to learning_signals.jsonl.
        """
        try:
            signal = {
                'event_type': 'mission_executed',
                'mission_id': mission_id,
                'execution_status': status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            
            if result:
                signal['execution_result'] = {
                    'success': result.get('success'),
                    'tools_used': result.get('tools_used', []),
                }
            
            if error:
                signal['error'] = error
            
            # Append to learning_signals.jsonl
            with open(self.signals_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(signal) + '\n')
            
            logger.info(f"[EXECUTOR] Emitted signal: {mission_id} execution {status}")
        
        except Exception as e:
            logger.error(f"[EXECUTOR] Error emitting signal: {e}", exc_info=True)
    
    async def run_executor_loop(self) -> None:
        """
        Main executor loop.
        
        Continuously dequeues and executes missions.
        Non-blocking: yields control periodically.
        """
        self.running = True
        logger.info("[EXECUTOR] Executor loop started")
        
        try:
            while self.running:
                # Check for queued missions
                if not execution_queue.is_empty():
                    mission_data = execution_queue.dequeue()
                    if mission_data:
                        await self.execute_mission(mission_data)
                
                # Yield control every loop iteration
                await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"[EXECUTOR] Executor loop error: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("[EXECUTOR] Executor loop stopped")
    
    def stop(self) -> None:
        """Stop the executor loop."""
        self.running = False


# Global executor (singleton)
executor = MissionExecutor()

