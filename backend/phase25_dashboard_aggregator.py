"""
Phase 25: Dashboard Data Aggregator

Reads Phase 24 outputs and Phase 25 goals/tasks to feed three integrated dashboards:
- Operations Dashboard: Real-time execution, conflicts, rollbacks
- Learning Dashboard: Competitor insights, GHL trends
- Side Hustle Dashboard: Revenue opportunities, ROI metrics
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from backend.learning.signal_priority import apply_signal_priority


@dataclass
class DashboardData:
    """Unified dashboard data structure"""
    timestamp: str
    operations: Dict[str, Any]
    learning: Dict[str, Any]
    side_hustle: Dict[str, Any]


class Phase25DashboardAggregator:
    """Aggregates data from Phase 24 and Phase 25 for dashboard consumption"""
    
    def __init__(self, data_dir: str = "./outputs/phase25"):
        self.data_dir = Path(data_dir)
        self.phase24_dir = Path("./outputs/phase24")
        
        # Phase 25 files
        self.goals_file = self.data_dir / "goals.jsonl"
        self.tasks_file = self.data_dir / "tasks.jsonl"
        self.execution_log = self.data_dir / "tool_execution_log.jsonl"
        
        # Phase 24 files
        self.phase24_conflicts = self.phase24_dir / "tool_conflicts.json"
        self.phase24_rollbacks = self.phase24_dir / "rollback_events.jsonl"
        self.phase24_health = self.phase24_dir / "system_health.json"
    
    def get_operations_dashboard_data(self) -> Dict[str, Any]:
        """Data for Operations Dashboard: real-time execution, conflicts, rollbacks"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_goals": self._get_active_goals(),
            "active_goals_count": self._count_active_goals(),
            "active_missions": self._get_recent_missions(limit=10),
            "active_missions_count": len(self._get_recent_missions(limit=10)),
            "active_tasks": self._count_active_tasks(),
            "execution_mode": "LIVE",
            "recent_executions": self._get_recent_executions(limit=10),
            "unresolved_conflicts": self._get_unresolved_conflicts(),
            "recent_rollbacks": self._get_recent_rollbacks(limit=5),
            "system_health": self._get_system_health(),
            "task_distribution": self._get_task_distribution()
        }
    
    def get_learning_dashboard_data(self) -> Dict[str, Any]:
        """Data for Learning Dashboard: market insights, GHL trends, competitor research"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "competitor_insights": self._get_competitor_insights(),
            "ghl_campaign_trends": self._get_ghl_trends(),
            "lead_enrichment_status": self._get_lead_enrichment_status(),
            "market_opportunities": self._get_market_opportunities(),
            "learning_signals": self._get_learning_signals(limit=10),
            "success_metrics": self._get_success_metrics()
        }
    
    def get_side_hustle_dashboard_data(self) -> Dict[str, Any]:
        """Data for Side Hustle Dashboard: revenue opportunities, ROI tracking"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_opportunities": self._get_active_opportunities(),
            "revenue_potential": self._calculate_revenue_potential(),
            "opportunity_roi": self._get_roi_analysis(),
            "automated_tasks": self._get_automated_tasks(),
            "income_streams": self._get_income_streams(),
            "daily_summary": self._get_daily_revenue_summary()
        }
    
    # ==================== OPERATIONS DASHBOARD METHODS ====================
    
    def _count_active_goals(self) -> int:
        """Count goals with status IN_PROGRESS or APPROVED"""
        count = 0
        try:
            if self.goals_file.exists():
                with open(self.goals_file, 'r') as f:
                    for line in f:
                        goal = json.loads(line)
                        if goal.get('status') in ['in_progress', 'approved']:
                            count += 1
        except:
            pass
        return count
    
    def _get_active_goals(self) -> List[Dict[str, Any]]:
        """
        Return full active goal objects for UI consumption.
        Active = status in ['in_progress', 'approved']
        This method supports frontend rendering while maintaining backward compatibility.
        """
        goals = []
        try:
            if self.goals_file.exists():
                with open(self.goals_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            goal = json.loads(line)
                            if goal.get('status') in ['in_progress', 'approved']:
                                goals.append(goal)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            # Log error but don't crash
            import logging
            logging.error(f"Error reading goals: {e}")
        return goals
    
    def _count_active_tasks(self) -> int:
        """Count tasks with status IN_PROGRESS"""
        count = 0
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    for line in f:
                        task = json.loads(line)
                        if task.get('status') == 'in_progress':
                            count += 1
        except:
            pass
        return count
    
    def _get_recent_missions(self, limit: int = 10) -> List[Dict]:
        """Get most recent missions from missions.jsonl"""
        missions = []
        try:
            missions_file = Path("outputs/phase25/missions.jsonl")
            if missions_file.exists():
                with open(missions_file, 'r') as f:
                    for line in f:
                        event = json.loads(line)
                        # Only include mission_created events
                        if event.get('event_type') == 'mission_created':
                            mission = event.get('mission', {})
                            missions.append({
                                'mission_id': mission.get('mission_id'),
                                'objective': mission.get('objective', {}).get('description', 'Unknown'),
                                'status': mission.get('status', 'unknown'),
                                'created_at': mission.get('created_at')
                            })
            # Return most recent
            return missions[-limit:] if len(missions) > limit else missions
        except:
            return []
    
    def _get_recent_executions(self, limit: int = 10) -> List[Dict]:
        """Get most recent tool executions"""
        executions = []
        try:
            if self.execution_log.exists():
                with open(self.execution_log, 'r') as f:
                    for line in f:
                        exec_data = json.loads(line)
                        executions.append(exec_data)
            # Return most recent
            return executions[-limit:] if len(executions) > limit else executions
        except:
            return []
    
    def _get_unresolved_conflicts(self) -> List[Dict]:
        """Get unresolved tool conflicts from Phase 24"""
        try:
            if self.phase24_conflicts.exists():
                with open(self.phase24_conflicts, 'r') as f:
                    conflicts = json.load(f)
                    if isinstance(conflicts, list):
                        return [c for c in conflicts if c.get('resolution_status') != 'resolved']
        except:
            pass
        return []
    
    def _get_recent_rollbacks(self, limit: int = 5) -> List[Dict]:
        """Get recent rollback events from Phase 24"""
        rollbacks = []
        try:
            if self.phase24_rollbacks.exists():
                with open(self.phase24_rollbacks, 'r') as f:
                    for line in f:
                        rb = json.loads(line)
                        rollbacks.append(rb)
            return rollbacks[-limit:] if len(rollbacks) > limit else rollbacks
        except:
            pass
        return []
    
    def _get_system_health(self) -> Dict:
        """Get system health snapshot from Phase 24"""
        try:
            if self.phase24_health.exists():
                with open(self.phase24_health, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            "health_score": 85.0,
            "execution_mode": "LIVE",
            "active_tools": 0,
            "anomalies": []
        }
    
    def _get_task_distribution(self) -> Dict[str, int]:
        """Distribution of tasks by type"""
        distribution = {}
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    for line in f:
                        task = json.loads(line)
                        task_type = task.get('task_type', 'unknown')
                        distribution[task_type] = distribution.get(task_type, 0) + 1
        except:
            pass
        return distribution
    
    # ==================== LEARNING DASHBOARD METHODS ====================
    
    def _get_competitor_insights(self) -> List[Dict]:
        """Competitor research results from web scraping tasks"""
        insights = []
        try:
            if self.execution_log.exists():
                with open(self.execution_log, 'r') as f:
                    for line in f:
                        exec_data = json.loads(line)
                        if 'research' in exec_data.get('action_type', ''):
                            insights.append({
                                "timestamp": exec_data.get('timestamp'),
                                "source": exec_data.get('tool_name'),
                                "data": exec_data.get('data_extracted', {})
                            })
        except:
            pass
        return insights[-5:] if len(insights) > 5 else insights
    
    def _get_ghl_trends(self) -> Dict[str, Any]:
        """GHL campaign performance trends"""
        return {
            "total_campaigns": 0,
            "published": 0,
            "draft": 0,
            "success_rate": 0.0,
            "avg_lead_quality": 0.0
        }
    
    def _get_lead_enrichment_status(self) -> Dict:
        """Status of lead enrichment operations"""
        return {
            "total_leads": 0,
            "enriched": 0,
            "pending": 0,
            "quality_score": 0.0
        }
    
    def _get_market_opportunities(self) -> List[Dict]:
        """Discovered market opportunities"""
        return []
    
    def _get_learning_signals(self, limit: int = 10) -> List[Dict]:
        """Recent learning signals (no filtering to avoid signal loss)."""
        signals = []
        signals_file = self.data_dir / "learning_signals.jsonl"
        try:
            if signals_file.exists():
                with open(signals_file, 'r') as f:
                    for line in f:
                        sig = json.loads(line)
                        signals.append(apply_signal_priority(sig))
            return signals[-limit:] if len(signals) > limit else signals
        except:
            pass
        return []
    
    def _get_success_metrics(self) -> Dict[str, float]:
        """Overall success metrics"""
        return {
            "task_success_rate": 0.0,
            "goal_completion_rate": 0.0,
            "average_confidence": 0.0
        }
    
    # ==================== SIDE HUSTLE DASHBOARD METHODS ====================
    
    def _get_active_opportunities(self) -> List[Dict]:
        """Active revenue opportunities"""
        opportunities = []
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    for line in f:
                        task = json.loads(line)
                        if task.get('task_type') == 'side_hustle' and task.get('status') != 'completed':
                            opportunities.append({
                                "opportunity_id": task.get('task_id'),
                                "type": task.get('parameters', {}).get('opportunity_type', 'unknown'),
                                "status": task.get('status'),
                                "roi_potential": task.get('parameters', {}).get('roi_potential', 0)
                            })
        except:
            pass
        return opportunities
    
    def _calculate_revenue_potential(self) -> Dict[str, float]:
        """Calculate total revenue potential"""
        return {
            "daily_potential": 0.0,
            "weekly_potential": 0.0,
            "monthly_potential": 0.0,
            "total_potential": 0.0
        }
    
    def _get_roi_analysis(self) -> List[Dict]:
        """ROI analysis by opportunity type"""
        return []
    
    def _get_automated_tasks(self) -> List[Dict]:
        """Automated side hustle tasks"""
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    tasks = []
                    for line in f:
                        task = json.loads(line)
                        if task.get('task_type') == 'side_hustle':
                            tasks.append({
                                "task_id": task.get('task_id'),
                                "type": task.get('parameters', {}).get('opportunity_type'),
                                "status": task.get('status'),
                                "created_at": task.get('created_at')
                            })
                    return tasks[-10:] if len(tasks) > 10 else tasks
        except:
            pass
        return []
    
    def _get_income_streams(self) -> List[Dict]:
        """Income streams breakdown"""
        return [
            {"name": "Freelance", "monthly_target": 0, "current": 0},
            {"name": "Affiliate", "monthly_target": 0, "current": 0},
            {"name": "Lead Resale", "monthly_target": 0, "current": 0}
        ]
    
    def _get_daily_revenue_summary(self) -> Dict:
        """Daily revenue summary"""
        return {
            "today_revenue": 0.0,
            "daily_average": 0.0,
            "goal": 0.0,
            "projected_monthly": 0.0
        }


# Global aggregator instance
dashboard_aggregator = Phase25DashboardAggregator()
