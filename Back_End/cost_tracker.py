"""
Cost Tracker: Measures ACTUAL costs after execution

Compares:
- Estimated vs actual SerpAPI searches
- Estimated vs actual OpenAI tokens/cost
- Records variance for learning

Purpose: Improve cost estimation accuracy over time.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from Back_End.cost_estimator import MissionCost, ServiceTier, ModelType, CostEstimator

logger = logging.getLogger(__name__)


class CostTracker:
    """
    Tracks actual API costs after execution and compares to estimates.
    
    Extracts usage from API responses and calculates actual costs.
    """
    
    def __init__(self, storage_path: str = 'data/cost_reconciliation.jsonl'):
        """
        Initialize cost tracker.
        
        Args:
            storage_path: Path to cost reconciliation storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure file exists
        if not self.storage_path.exists():
            self.storage_path.touch()
            logger.info(f"Created cost reconciliation storage: {self.storage_path}")
        
        self.cost_estimator = CostEstimator()
    
    def extract_api_usage(self, tool_name: str, tool_response: Dict) -> Dict[str, Any]:
        """
        Extract actual usage from API responses.
        
        Args:
            tool_name: Name of tool executed
            tool_response: Response from tool execution
            
        Returns:
            {
                'serpapi_searches': int,
                'openai_input_tokens': int,
                'openai_output_tokens': int,
                'firestore_reads': int,
                'firestore_writes': int
            }
        """
        usage = {}
        
        # SerpAPI tools (each call = 1 search)
        if tool_name in ['web_search', 'web_research', 'serp_search']:
            usage['serpapi_searches'] = 1
            logger.debug(f"[COST_TRACKER] Detected SerpAPI usage: 1 search")
        
        # OpenAI usage (from response.usage if available)
        if 'usage' in tool_response:
            usage_data = tool_response['usage']
            usage['openai_input_tokens'] = usage_data.get('input_tokens', 0) or usage_data.get('prompt_tokens', 0)
            usage['openai_output_tokens'] = usage_data.get('output_tokens', 0) or usage_data.get('completion_tokens', 0)
            logger.debug(
                f"[COST_TRACKER] Detected OpenAI usage: "
                f"{usage['openai_input_tokens']} input, {usage['openai_output_tokens']} output tokens"
            )
        
        # Firestore usage (if available in response)
        if 'firestore_operations' in tool_response:
            ops = tool_response['firestore_operations']
            usage['firestore_reads'] = ops.get('reads', 0)
            usage['firestore_writes'] = ops.get('writes', 0)
            logger.debug(
                f"[COST_TRACKER] Detected Firestore usage: "
                f"{usage.get('firestore_reads', 0)} reads, {usage.get('firestore_writes', 0)} writes"
            )
        
        return usage
    
    def calculate_actual_cost(
        self,
        usage: Dict[str, Any],
        tier: ServiceTier = ServiceTier.FREE,
        model: ModelType = ModelType.GPT_4O_MINI
    ) -> Dict[str, Any]:
        """
        Calculate actual costs from usage.
        
        Args:
            usage: Usage data from extract_api_usage()
            tier: Current SerpAPI tier
            model: OpenAI model used
            
        Returns:
            {
                'serpapi_credits_consumed': int,  # Not dollars!
                'openai_cost_usd': float,
                'firestore_cost_usd': float,
                'total_dollar_cost': float  # Only variable costs
            }
        """
        # SerpAPI: Track credits, not dollars (already paid fixed fee)
        serpapi_credits = usage.get('serpapi_searches', 0)
        
        # OpenAI: Calculate actual dollar cost from tokens
        openai_cost = 0.0
        input_tokens = usage.get('openai_input_tokens', 0)
        output_tokens = usage.get('openai_output_tokens', 0)
        
        if input_tokens or output_tokens:
            pricing = self.cost_estimator.OPENAI_PRICING[model]
            input_cost = (input_tokens / 1_000_000) * pricing['input']
            output_cost = (output_tokens / 1_000_000) * pricing['output']
            openai_cost = input_cost + output_cost
            logger.debug(f"[COST_TRACKER] OpenAI cost: ${openai_cost:.6f}")
        
        # Firestore: Calculate actual dollar cost
        firestore_cost = 0.0
        reads = usage.get('firestore_reads', 0)
        writes = usage.get('firestore_writes', 0)
        
        if reads or writes:
            read_cost = (reads / 100_000) * self.cost_estimator.FIRESTORE_PRICING['read_per_100k']
            write_cost = (writes / 100_000) * self.cost_estimator.FIRESTORE_PRICING['write_per_100k']
            firestore_cost = read_cost + write_cost
            logger.debug(f"[COST_TRACKER] Firestore cost: ${firestore_cost:.6f}")
        
        total_dollar_cost = openai_cost + firestore_cost
        
        return {
            'serpapi_credits_consumed': serpapi_credits,
            'openai_cost_usd': round(openai_cost, 6),
            'firestore_cost_usd': round(firestore_cost, 6),
            'total_dollar_cost': round(total_dollar_cost, 6)
        }
    
    def reconcile(
        self,
        mission_id: str,
        estimated_cost: MissionCost,
        actual_usage: Dict[str, Any],
        tier: ServiceTier = ServiceTier.FREE,
        model: ModelType = ModelType.GPT_4O_MINI
    ) -> Dict[str, Any]:
        """
        Compare estimated vs actual costs and create reconciliation record.
        
        Args:
            mission_id: Mission identifier
            estimated_cost: Original cost estimate
            actual_usage: Actual usage from extract_api_usage()
            tier: SerpAPI tier used
            model: OpenAI model used
            
        Returns:
            Reconciliation record with variance analysis
        """
        # Calculate actual costs
        actual = self.calculate_actual_cost(actual_usage, tier, model)
        
        # Extract estimated values
        estimated_serpapi_searches = 0
        estimated_openai_cost = 0.0
        estimated_firestore_cost = 0.0
        
        for service_cost in estimated_cost.service_costs:
            if service_cost.service == 'serpapi':
                estimated_serpapi_searches = service_cost.operation_count
            elif service_cost.service == 'openai':
                estimated_openai_cost += service_cost.total_cost
            elif service_cost.service == 'firestore':
                estimated_firestore_cost += service_cost.total_cost
        
        # Calculate variances
        serpapi_variance = actual['serpapi_credits_consumed'] - estimated_serpapi_searches
        openai_variance = actual['openai_cost_usd'] - estimated_openai_cost
        dollar_variance = actual['total_dollar_cost'] - (estimated_openai_cost + estimated_firestore_cost)
        
        # Calculate accuracy (0.0-1.0)
        if estimated_cost.total_usd > 0:
            accuracy = 1.0 - min(1.0, abs(dollar_variance) / estimated_cost.total_usd)
        else:
            accuracy = 1.0 if actual['total_dollar_cost'] == 0 else 0.0
        
        reconciliation = {
            'mission_id': mission_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'tier': tier.value,
            'model': model.value,
            
            # Credits (SerpAPI) - not dollar amounts
            'serpapi': {
                'estimated_searches': estimated_serpapi_searches,
                'actual_searches': actual['serpapi_credits_consumed'],
                'variance': serpapi_variance
            },
            
            # Dollars (OpenAI)
            'openai': {
                'estimated_usd': round(estimated_openai_cost, 6),
                'actual_usd': actual['openai_cost_usd'],
                'variance_usd': round(openai_variance, 6),
                'variance_percent': round((openai_variance / estimated_openai_cost * 100) if estimated_openai_cost > 0 else 0, 2)
            },
            
            # Dollars (Firestore)
            'firestore': {
                'estimated_usd': round(estimated_firestore_cost, 6),
                'actual_usd': actual['firestore_cost_usd'],
                'variance_usd': round(actual['firestore_cost_usd'] - estimated_firestore_cost, 6)
            },
            
            # Totals
            'total_estimated_usd': round(estimated_cost.total_usd, 6),
            'total_actual_usd': actual['total_dollar_cost'],
            'total_variance_usd': round(dollar_variance, 6),
            'estimation_accuracy': round(accuracy, 4)
        }
        
        # Write to storage
        self._write_reconciliation(reconciliation)
        
        logger.info(
            f"[COST_TRACKER] Reconciliation: ${actual['total_dollar_cost']:.4f} actual "
            f"vs ${estimated_cost.total_usd:.4f} estimated (accuracy: {accuracy:.2%})"
        )
        
        return reconciliation
    
    def _write_reconciliation(self, reconciliation: Dict):
        """Write reconciliation record to storage"""
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(reconciliation) + '\n')
    
    def get_estimation_accuracy_stats(self, last_n: int = 100) -> Dict[str, Any]:
        """
        Get accuracy statistics from recent reconciliations.
        
        Args:
            last_n: Number of recent reconciliations to analyze
            
        Returns:
            {
                'average_accuracy': float,
                'total_reconciliations': int,
                'average_variance_usd': float
            }
        """
        if not self.storage_path.exists():
            return {
                'average_accuracy': 0.0,
                'total_reconciliations': 0,
                'average_variance_usd': 0.0
            }
        
        accuracies = []
        variances = []
        
        with open(self.storage_path, 'r') as f:
            lines = f.readlines()
            for line in lines[-last_n:]:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    accuracies.append(record.get('estimation_accuracy', 0))
                    variances.append(abs(record.get('total_variance_usd', 0)))
                except json.JSONDecodeError:
                    continue
        
        if not accuracies:
            return {
                'average_accuracy': 0.0,
                'total_reconciliations': 0,
                'average_variance_usd': 0.0
            }
        
        return {
            'average_accuracy': round(sum(accuracies) / len(accuracies), 4),
            'total_reconciliations': len(accuracies),
            'average_variance_usd': round(sum(variances) / len(variances), 6)
        }


# Singleton instance
_cost_tracker = None


def get_cost_tracker() -> CostTracker:
    """Get or create cost tracker singleton"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker

