"""
Phase 6: Multi-Agent Coordination
Manages multiple BuddyLocalAgent instances with coordination, communication, and work distribution.

Architecture:
- AgentRegistry: Tracks all active agents and their capabilities
- AgentCoordinator: Orchestrates multi-agent workflows and task distribution
- WorkDistributor: Intelligently distributes work across agents
- AgentHealthMonitor: Monitors agent health and handles failover
- SharedStateManager: Manages shared state across agents
"""

import sqlite3
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Set, Tuple, Callable
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent health status"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    STARTING = "starting"


class CoordinationStrategy(Enum):
    """Task distribution strategies"""
    ROUND_ROBIN = "round_robin"          # Distribute tasks in sequence
    LEAST_BUSY = "least_busy"            # Send to agent with lowest queue
    LOAD_BALANCED = "load_balanced"      # Weight by resources + queue
    CAPABILITY_MATCH = "capability_match"  # Match agent capabilities
    LOCALITY = "locality"                # Prefer local/nearby agents


class FailoverStrategy(Enum):
    """Failover scenarios"""
    IMMEDIATE_RETRY = "immediate_retry"    # Retry immediately on another agent
    QUEUED_RETRY = "queued_retry"          # Queue task for retry later
    ESCALATE = "escalate"                   # Move to supervisor agent
    MARK_FAILED = "mark_failed"             # Mark as failed


@dataclass
class AgentCapability:
    """Represents what an agent can do"""
    name: str                       # Capability name (e.g., "screenshot", "navigate")
    supported: bool = True          # Whether supported
    max_concurrent: int = 10        # Max concurrent operations
    version: str = "1.0"           # Capability version
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentInfo:
    """Information about a registered agent"""
    agent_id: str                   # Unique agent ID
    hostname: str                   # Host running the agent
    port: int                       # Port for communication
    status: AgentStatus = AgentStatus.STARTING
    resource_capacity: Dict[str, Any] = field(default_factory=dict)  # CPU, memory, browsers
    current_workload: int = 0       # Tasks currently being processed
    max_workload: int = 50          # Maximum concurrent tasks
    capabilities: Dict[str, AgentCapability] = field(default_factory=dict)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    
    def is_healthy(self, heartbeat_timeout: int = 30) -> bool:
        """Check if agent is responding"""
        elapsed = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return elapsed < heartbeat_timeout and self.status != AgentStatus.OFFLINE
    
    def get_availability(self) -> float:
        """Get availability ratio (0.0 - 1.0)"""
        if self.max_workload == 0:
            return 0.0
        return max(0.0, (self.max_workload - self.current_workload) / self.max_workload)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['last_heartbeat'] = self.last_heartbeat.isoformat()
        data['registered_at'] = self.registered_at.isoformat()
        data['capabilities'] = {k: v.to_dict() for k, v in self.capabilities.items()}
        return data


@dataclass
class CoordinatedTask:
    """Task distributed across multiple agents"""
    task_id: str                    # Unique task ID
    agent_id: Optional[str] = None  # Assigned to agent
    subtasks: List[str] = field(default_factory=list)  # Subtask IDs
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # Task dependencies
    status: str = "pending"         # pending, assigned, in_progress, completed, failed
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['assigned_at'] = self.assigned_at.isoformat() if self.assigned_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data


class AgentRegistry:
    """Registry and discovery for all agents in the system"""
    
    def __init__(self, db_path: str = "./buddy_agents.db"):
        self.db_path = db_path
        self.local_agents: Dict[str, AgentInfo] = {}
        self.lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database for agent registration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                hostname TEXT NOT NULL,
                port INTEGER NOT NULL,
                agent_data TEXT NOT NULL,
                registered_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_capabilities (
                agent_id TEXT,
                capability_name TEXT,
                capability_data TEXT,
                PRIMARY KEY (agent_id, capability_name),
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_agent(self, hostname: str, port: int, 
                      resource_capacity: Dict[str, Any],
                      capabilities: Dict[str, AgentCapability]) -> str:
        """Register a new agent and return agent_id"""
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        
        agent_info = AgentInfo(
            agent_id=agent_id,
            hostname=hostname,
            port=port,
            resource_capacity=resource_capacity,
            capabilities=capabilities,
            status=AgentStatus.ACTIVE
        )
        
        with self.lock:
            self.local_agents[agent_id] = agent_info
            
            # Persist to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO agents 
                (agent_id, hostname, port, agent_data, registered_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                agent_id, hostname, port,
                json.dumps(agent_info.to_dict()),
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            conn.close()
        
        logger.info(f"Registered agent {agent_id} on {hostname}:{port}")
        return agent_id
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent info by ID"""
        with self.lock:
            return self.local_agents.get(agent_id)
    
    def get_all_agents(self, status_filter: Optional[AgentStatus] = None) -> List[AgentInfo]:
        """Get all agents, optionally filtered by status"""
        with self.lock:
            agents = list(self.local_agents.values())
            if status_filter:
                agents = [a for a in agents if a.status == status_filter]
            return agents
    
    def update_agent_status(self, agent_id: str, status: AgentStatus):
        """Update agent status"""
        with self.lock:
            if agent_id in self.local_agents:
                self.local_agents[agent_id].status = status
                self.local_agents[agent_id].last_heartbeat = datetime.utcnow()
    
    def update_agent_workload(self, agent_id: str, workload: int):
        """Update current workload for agent"""
        with self.lock:
            if agent_id in self.local_agents:
                self.local_agents[agent_id].current_workload = workload
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        with self.lock:
            if agent_id in self.local_agents:
                del self.local_agents[agent_id]
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
                cursor.execute("DELETE FROM agent_capabilities WHERE agent_id = ?", (agent_id,))
                conn.commit()
                conn.close()
                
                logger.info(f"Unregistered agent {agent_id}")


class WorkDistributor:
    """Distributes work across multiple agents"""
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
    
    def select_agent(self, strategy: CoordinationStrategy = CoordinationStrategy.LOAD_BALANCED,
                    required_capability: Optional[str] = None) -> Optional[str]:
        """Select best agent for task based on strategy"""
        agents = self.registry.get_all_agents(status_filter=AgentStatus.ACTIVE)
        healthy_agents = [a for a in agents if a.is_healthy()]
        
        if not healthy_agents:
            return None
        
        # Filter by required capability
        if required_capability:
            healthy_agents = [
                a for a in healthy_agents 
                if required_capability in a.capabilities
            ]
        
        if not healthy_agents:
            return None
        
        if strategy == CoordinationStrategy.ROUND_ROBIN:
            return healthy_agents[0].agent_id
        
        elif strategy == CoordinationStrategy.LEAST_BUSY:
            agent = min(healthy_agents, key=lambda a: a.current_workload)
            return agent.agent_id
        
        elif strategy == CoordinationStrategy.LOAD_BALANCED:
            # Score based on availability and resources
            scored = [
                (a.agent_id, a.get_availability() * (1 - a.current_workload / a.max_workload))
                for a in healthy_agents
            ]
            agent_id = max(scored, key=lambda x: x[1])[0]
            return agent_id
        
        elif strategy == CoordinationStrategy.CAPABILITY_MATCH:
            # Already filtered by capability above
            return healthy_agents[0].agent_id
        
        else:
            return healthy_agents[0].agent_id
    
    def distribute_tasks(self, tasks: List[Dict[str, Any]], 
                        strategy: CoordinationStrategy = CoordinationStrategy.LOAD_BALANCED
                        ) -> Dict[str, str]:
        """Distribute multiple tasks across agents"""
        assignments = {}
        for task in tasks:
            agent_id = self.select_agent(strategy)
            if agent_id:
                assignments[task.get('task_id')] = agent_id
        return assignments


class AgentHealthMonitor:
    """Monitors agent health and handles failover"""
    
    def __init__(self, registry: AgentRegistry, heartbeat_interval: int = 10,
                 heartbeat_timeout: int = 30):
        self.registry = registry
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.monitor_thread = None
        self.running = False
    
    def start(self):
        """Start health monitoring"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Agent health monitor started")
    
    def stop(self):
        """Stop health monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Agent health monitor stopped")
    
    def _monitor_loop(self):
        """Continuous monitoring loop"""
        while self.running:
            try:
                agents = self.registry.get_all_agents()
                for agent in agents:
                    if not agent.is_healthy(self.heartbeat_timeout):
                        logger.warning(f"Agent {agent.agent_id} is unresponsive")
                        self.registry.update_agent_status(agent.agent_id, AgentStatus.OFFLINE)
                    elif agent.status == AgentStatus.OFFLINE and agent.is_healthy():
                        logger.info(f"Agent {agent.agent_id} recovered")
                        self.registry.update_agent_status(agent.agent_id, AgentStatus.ACTIVE)
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
            
            time.sleep(self.heartbeat_interval)
    
    def record_heartbeat(self, agent_id: str):
        """Record heartbeat from agent"""
        agent = self.registry.get_agent(agent_id)
        if agent:
            agent.last_heartbeat = datetime.utcnow()


class SharedStateManager:
    """Manages shared state across agents"""
    
    def __init__(self, db_path: str = "./buddy_shared_state.db"):
        self.db_path = db_path
        self.shared_state: Dict[str, Any] = {}
        self.lock = threading.RLock()
        self._init_db()
        self._load_state()
    
    def _init_db(self):
        """Initialize shared state database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                agent_id TEXT,
                updated_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_state(self):
        """Load all state from database into memory"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM shared_state")
            
            for key, value in cursor.fetchall():
                try:
                    self.shared_state[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    self.shared_state[key] = value
            
            conn.close()
    
    def set_state(self, key: str, value: Any, agent_id: str):
        """Set shared state value"""
        with self.lock:
            self.shared_state[key] = value
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO shared_state 
                (key, value, agent_id, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, json.dumps(value), agent_id, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
    
    def get_state(self, key: str) -> Optional[Any]:
        """Get shared state value"""
        with self.lock:
            return self.shared_state.get(key)
    
    def get_all_state(self) -> Dict[str, Any]:
        """Get all shared state"""
        with self.lock:
            return dict(self.shared_state)


class AgentCoordinator:
    """Main coordinator for multi-agent system"""
    
    def __init__(self, db_path: str = "./buddy_coordinator.db"):
        self.db_path = db_path
        self.registry = AgentRegistry()
        self.distributor = WorkDistributor(self.registry)
        self.health_monitor = AgentHealthMonitor(self.registry)
        self.shared_state = SharedStateManager()
        self.coordinated_tasks: Dict[str, CoordinatedTask] = {}
        self.lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """Initialize coordinator database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coordinated_tasks (
                task_id TEXT PRIMARY KEY,
                task_data TEXT,
                agent_id TEXT,
                status TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def start(self):
        """Start the coordinator"""
        self.health_monitor.start()
        logger.info("Agent coordinator started")
    
    def stop(self):
        """Stop the coordinator"""
        self.health_monitor.stop()
        logger.info("Agent coordinator stopped")
    
    def register_agent(self, hostname: str, port: int,
                      resource_capacity: Dict[str, Any],
                      capabilities: Dict[str, AgentCapability]) -> str:
        """Register a new agent"""
        return self.registry.register_agent(hostname, port, resource_capacity, capabilities)
    
    def submit_task(self, task_id: str, subtasks: List[str],
                   strategy: CoordinationStrategy = CoordinationStrategy.LOAD_BALANCED
                   ) -> bool:
        """Submit a coordinated task"""
        task = CoordinatedTask(
            task_id=task_id,
            subtasks=subtasks,
            status="pending"
        )
        
        # Find best agent
        agent_id = self.distributor.select_agent(strategy)
        if not agent_id:
            logger.error(f"No suitable agent found for task {task_id}")
            return False
        
        task.agent_id = agent_id
        task.status = "assigned"
        task.assigned_at = datetime.utcnow()
        
        with self.lock:
            self.coordinated_tasks[task_id] = task
            
            # Persist
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO coordinated_tasks
                (task_id, task_data, agent_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                task_id, json.dumps(task.to_dict()), agent_id, task.status,
                task.created_at.isoformat(), datetime.utcnow().isoformat()
            ))
            conn.commit()
            conn.close()
        
        logger.info(f"Task {task_id} assigned to agent {agent_id}")
        return True
    
    def record_task_result(self, task_id: str, result: Any, error: Optional[str] = None):
        """Record task completion"""
        with self.lock:
            if task_id in self.coordinated_tasks:
                task = self.coordinated_tasks[task_id]
                task.status = "failed" if error else "completed"
                task.result = result
                task.error = error
                task.completed_at = datetime.utcnow()
                
                if task.agent_id:
                    agent = self.registry.get_agent(task.agent_id)
                    if agent:
                        if error:
                            agent.total_tasks_failed += 1
                        else:
                            agent.total_tasks_completed += 1
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get status of a coordinated task"""
        with self.lock:
            task = self.coordinated_tasks.get(task_id)
            return task.status if task else None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        agents = self.registry.get_all_agents()
        
        active_agents = sum(1 for a in agents if a.status == AgentStatus.ACTIVE)
        total_capacity = sum(a.max_workload for a in agents)
        total_workload = sum(a.current_workload for a in agents)
        total_completed = sum(a.total_tasks_completed for a in agents)
        total_failed = sum(a.total_tasks_failed for a in agents)
        
        return {
            'total_agents': len(agents),
            'active_agents': active_agents,
            'total_capacity': total_capacity,
            'current_workload': total_workload,
            'capacity_utilization': total_workload / total_capacity if total_capacity > 0 else 0,
            'total_tasks_completed': total_completed,
            'total_tasks_failed': total_failed,
            'agents': [a.to_dict() for a in agents],
            'timestamp': datetime.utcnow().isoformat()
        }


def init_phase6_tables(db_paths: Dict[str, str]):
    """Initialize all Phase 6 database tables"""
    coordinator = AgentCoordinator(db_paths.get('coordinator', './buddy_coordinator.db'))
    coordinator._init_db()
    coordinator.registry._init_db()
    coordinator.shared_state._init_db()
    logger.info("Phase 6 tables initialized")
    return coordinator
