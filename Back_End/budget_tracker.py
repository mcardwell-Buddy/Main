"""
Budget Tracker: Separates credit-based and dollar-based budgets

Credit-based (SerpAPI):
- Monthly quota allocation
- Daily recommended pace
- Rollover from unused credits
- Hard enforcement at quota limit

Dollar-based (OpenAI, Firestore):
- Running total of actual spend
- Soft limits (configurable)
- Real-time cost accumulation

Storage: data/budgets.jsonl (append-only log)
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from Back_End.cost_estimator import ServiceTier

logger = logging.getLogger(__name__)


@dataclass
class CreditBudget:
    """Monthly credit quota for SerpAPI"""
    service: str  # "serpapi"
    tier: str  # ServiceTier value
    
    # Monthly allocation
    monthly_quota: int  # 1000 for STARTER
    billing_period_start: str  # ISO format
    billing_period_end: str  # ISO format
    
    # Current usage
    credits_used: int  # Actual searches made
    credits_remaining: int  # monthly_quota - credits_used
    
    # Daily pacing
    daily_recommended: int  # monthly_quota / days_in_month
    days_remaining_in_month: int
    daily_rollover: int  # Unused credits from previous days
    
    def can_afford(self, credits_needed: int) -> bool:
        """Can we afford this many searches?"""
        return self.credits_remaining >= credits_needed
    
    def calculate_todays_budget(self) -> int:
        """Daily budget including rollover"""
        # Base daily allocation
        base = self.daily_recommended
        
        # Calculate rollover from under-usage
        start_dt = datetime.fromisoformat(self.billing_period_start.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        days_elapsed = max(1, (now - start_dt).days)
        
        expected_usage = self.daily_recommended * days_elapsed
        rollover = max(0, expected_usage - self.credits_used)
        
        return base + int(rollover)
    
    def pace_status(self) -> Dict:
        """Are we on pace for the month?"""
        start_dt = datetime.fromisoformat(self.billing_period_start.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        days_elapsed = max(1, (now - start_dt).days)
        
        daily_rate = self.credits_used / days_elapsed
        projected_monthly = daily_rate * 30
        
        return {
            'on_pace': projected_monthly <= self.monthly_quota,
            'projected_usage': int(projected_monthly),
            'daily_rate': round(daily_rate, 2),
            'pace': 'ahead' if daily_rate < self.daily_recommended else 'behind'
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class DollarBudget:
    """Monthly dollar budget for OpenAI/Firestore"""
    service: str  # "openai" or "firestore"
    
    # Budget limits (configurable)
    monthly_limit_usd: float  # e.g., 100.00
    billing_period_start: str  # ISO format
    billing_period_end: str  # ISO format
    
    # Actual spending
    dollars_spent: float  # Running total
    dollars_remaining: float  # monthly_limit - dollars_spent
    
    def can_afford(self, cost_usd: float) -> bool:
        """Can we afford this cost?"""
        return self.dollars_remaining >= cost_usd
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class BudgetTracker:
    """Tracks both credit and dollar budgets with persistent storage"""
    
    # Tier quotas
    TIER_QUOTAS = {
        ServiceTier.FREE: 250,
        ServiceTier.STARTER: 1000,
        ServiceTier.GROWTH: 5000,
        ServiceTier.SCALE: 15000
    }
    
    def __init__(self, storage_path: str = 'data/budgets.jsonl'):
        """
        Initialize budget tracker.
        
        Args:
            storage_path: Path to budget storage file
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure file exists
        if not self.storage_path.exists():
            self.storage_path.touch()
            logger.info(f"Created budget storage: {self.storage_path}")
    
    def get_serpapi_budget(self, tier: ServiceTier = ServiceTier.FREE) -> CreditBudget:
        """
        Get current SerpAPI credit budget with rollover.
        
        Args:
            tier: Current SerpAPI tier
            
        Returns:
            CreditBudget with current state
        """
        # Get current billing period (first day of month)
        now = datetime.now(timezone.utc)
        billing_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        
        # Calculate billing end (first day of next month)
        if now.month == 12:
            billing_end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            billing_end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
        
        # Get total searches used this billing period
        credits_used = self._get_usage_this_period('serpapi', billing_start)
        
        # Calculate quotas
        monthly_quota = self.TIER_QUOTAS.get(tier, 250)
        days_in_month = (billing_end - billing_start).days
        daily_recommended = monthly_quota // days_in_month
        days_remaining = (billing_end - now).days
        
        # Calculate rollover
        days_elapsed = max(1, (now - billing_start).days)
        expected_usage = daily_recommended * days_elapsed
        daily_rollover = max(0, expected_usage - credits_used)
        
        return CreditBudget(
            service='serpapi',
            tier=tier.value,
            monthly_quota=monthly_quota,
            billing_period_start=billing_start.isoformat(),
            billing_period_end=billing_end.isoformat(),
            credits_used=credits_used,
            credits_remaining=monthly_quota - credits_used,
            daily_recommended=daily_recommended,
            days_remaining_in_month=days_remaining,
            daily_rollover=daily_rollover
        )
    
    def get_openai_budget(self, monthly_limit: float = 100.0) -> DollarBudget:
        """
        Get current OpenAI dollar budget.
        
        Args:
            monthly_limit: Monthly spending limit in USD
            
        Returns:
            DollarBudget with current state
        """
        # Get current billing period
        now = datetime.now(timezone.utc)
        billing_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        
        if now.month == 12:
            billing_end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            billing_end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
        
        # Get total dollars spent this period
        dollars_spent = self._get_spending_this_period('openai', billing_start)
        
        return DollarBudget(
            service='openai',
            monthly_limit_usd=monthly_limit,
            billing_period_start=billing_start.isoformat(),
            billing_period_end=billing_end.isoformat(),
            dollars_spent=dollars_spent,
            dollars_remaining=monthly_limit - dollars_spent
        )
    
    def get_firestore_budget(self, monthly_limit: float = 50.0) -> DollarBudget:
        """Get current Firestore dollar budget"""
        now = datetime.now(timezone.utc)
        billing_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        
        if now.month == 12:
            billing_end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            billing_end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
        
        dollars_spent = self._get_spending_this_period('firestore', billing_start)
        
        return DollarBudget(
            service='firestore',
            monthly_limit_usd=monthly_limit,
            billing_period_start=billing_start.isoformat(),
            billing_period_end=billing_end.isoformat(),
            dollars_spent=dollars_spent,
            dollars_remaining=monthly_limit - dollars_spent
        )
    
    def record_serpapi_usage(self, searches_used: int, mission_id: Optional[str] = None):
        """
        Record actual SerpAPI searches used.
        
        Args:
            searches_used: Number of searches consumed
            mission_id: Optional mission ID for tracking
        """
        record = {
            'event_type': 'serpapi_usage',
            'service': 'serpapi',
            'searches_used': searches_used,
            'mission_id': mission_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self._append_record(record)
        logger.info(f"[BUDGET] Recorded SerpAPI usage: {searches_used} searches")
    
    def record_openai_usage(self, cost_usd: float, mission_id: Optional[str] = None, tokens: Optional[Dict] = None):
        """
        Record actual OpenAI spending.
        
        Args:
            cost_usd: Actual cost in USD
            mission_id: Optional mission ID for tracking
            tokens: Optional token counts {'input': int, 'output': int}
        """
        record = {
            'event_type': 'openai_usage',
            'service': 'openai',
            'cost_usd': cost_usd,
            'tokens': tokens or {},
            'mission_id': mission_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self._append_record(record)
        logger.info(f"[BUDGET] Recorded OpenAI usage: ${cost_usd:.4f}")
    
    def record_firestore_usage(self, cost_usd: float, mission_id: Optional[str] = None, operations: Optional[Dict] = None):
        """Record actual Firestore spending"""
        record = {
            'event_type': 'firestore_usage',
            'service': 'firestore',
            'cost_usd': cost_usd,
            'operations': operations or {},
            'mission_id': mission_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self._append_record(record)
        logger.info(f"[BUDGET] Recorded Firestore usage: ${cost_usd:.4f}")
    
    def _get_usage_this_period(self, service: str, billing_start: datetime) -> int:
        """Get total searches used in current billing period"""
        total = 0
        
        if not self.storage_path.exists():
            return 0
        
        with open(self.storage_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if record.get('service') == service and record.get('event_type') == f'{service}_usage':
                        record_time = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                        if record_time >= billing_start:
                            total += record.get('searches_used', 0)
                except json.JSONDecodeError:
                    continue
        
        return total
    
    def _get_spending_this_period(self, service: str, billing_start: datetime) -> float:
        """Get total dollars spent in current billing period"""
        total = 0.0
        
        if not self.storage_path.exists():
            return 0.0
        
        with open(self.storage_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if record.get('service') == service and record.get('event_type') == f'{service}_usage':
                        record_time = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                        if record_time >= billing_start:
                            total += record.get('cost_usd', 0.0)
                except json.JSONDecodeError:
                    continue
        
        return total
    
    def _append_record(self, record: Dict):
        """Append record to storage file"""
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(record) + '\n')


# Singleton instance
_budget_tracker = None


def get_budget_tracker() -> BudgetTracker:
    """Get or create budget tracker singleton"""
    global _budget_tracker
    if _budget_tracker is None:
        _budget_tracker = BudgetTracker()
    return _budget_tracker

