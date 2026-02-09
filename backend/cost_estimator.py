"""
Cost Estimator: Real-time API cost calculation with tiered pricing

Calculates costs for:
- SerpAPI (tiered: Free, Starter, Growth, Scale)
- OpenAI (token-based: gpt-4o-mini, gpt-4o, gpt-5-mini, gpt-5)
- Firestore (reads, writes, storage)

Philosophy:
- Dev = free tier
- Starter tier ($25) until revenue
- Scale only after making money

NO execution. Pure calculation. Deterministic only.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ServiceTier(Enum):
    """Service tier levels."""
    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    SCALE = "scale"


class ModelType(Enum):
    """OpenAI model types."""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5 = "gpt-5"


@dataclass
class ServiceCost:
    """Cost for a single service."""
    service: str  # "serpapi", "openai", "firestore"
    operation_count: int
    unit_cost: float  # Cost per operation
    total_cost: float
    tier: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MissionCost:
    """Total cost estimate for a mission."""
    total_usd: float
    service_costs: List[ServiceCost]
    currency: str = "USD"
    tier_recommendations: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    estimated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'total_usd': round(self.total_usd, 4),
            'currency': self.currency,
            'service_costs': [
                {
                    'service': sc.service,
                    'operation_count': sc.operation_count,
                    'unit_cost': sc.unit_cost,
                    'total_cost': round(sc.total_cost, 4),
                    'tier': sc.tier,
                    'details': sc.details
                }
                for sc in self.service_costs
            ],
            'tier_recommendations': self.tier_recommendations,
            'warnings': self.warnings,
            'estimated_at': self.estimated_at
        }


class CostEstimator:
    """
    Calculates real-time API costs with tiered pricing.
    
    Pricing (as of Feb 2026):
    
    SerpAPI:
    - Free: 250 searches/month ($0)
    - Starter: 1000 searches/month ($25)
    - Growth: 5000 searches/month ($75)
    - Scale: 15000 searches/month ($150)
    
    OpenAI (per 1M tokens):
    - gpt-4o-mini: $0.15 input / $0.60 output
    - gpt-4o: $2.50 input / $10.00 output
    - gpt-5-mini: $0.25 input / $2.00 output
    - gpt-5: $1.25 input / $10.00 output
    
    Firestore:
    - Reads: $0.06 per 100k
    - Writes: $0.18 per 100k
    - Storage: $0.10 per GB-day
    """
    
    # SerpAPI pricing tiers (USD)
    SERPAPI_TIERS = {
        ServiceTier.FREE: {'monthly_searches': 250, 'monthly_cost': 0.00},
        ServiceTier.STARTER: {'monthly_searches': 1000, 'monthly_cost': 25.00},
        ServiceTier.GROWTH: {'monthly_searches': 5000, 'monthly_cost': 75.00},
        ServiceTier.SCALE: {'monthly_searches': 15000, 'monthly_cost': 150.00}
    }
    
    # OpenAI token pricing (USD per 1M tokens)
    OPENAI_PRICING = {
        ModelType.GPT_4O_MINI: {'input': 0.15, 'output': 0.60},
        ModelType.GPT_4O: {'input': 2.50, 'output': 10.00},
        ModelType.GPT_5_MINI: {'input': 0.25, 'output': 2.00},
        ModelType.GPT_5: {'input': 1.25, 'output': 10.00}
    }
    
    # Firestore pricing (USD)
    FIRESTORE_PRICING = {
        'read_per_100k': 0.06,
        'write_per_100k': 0.18,
        'storage_per_gb_day': 0.10
    }
    
    def __init__(self, current_serpapi_tier: ServiceTier = ServiceTier.FREE):
        """
        Initialize cost estimator.
        
        Args:
            current_serpapi_tier: Current SerpAPI subscription tier
        """
        self.current_serpapi_tier = current_serpapi_tier
        logger.info(f"CostEstimator initialized with SerpAPI tier: {current_serpapi_tier.value}")
    
    def estimate_mission_cost(
        self,
        serpapi_searches: int = 0,
        openai_calls: Optional[List[Dict[str, Any]]] = None,
        firestore_reads: int = 0,
        firestore_writes: int = 0
    ) -> MissionCost:
        """
        Estimate total cost for a mission.
        
        Args:
            serpapi_searches: Number of SerpAPI searches
            openai_calls: List of OpenAI calls with {'model': ModelType, 'input_tokens': int, 'output_tokens': int}
            firestore_reads: Number of Firestore document reads
            firestore_writes: Number of Firestore document writes
            
        Returns:
            MissionCost: Complete cost breakdown
        """
        service_costs = []
        warnings = []
        tier_recommendations = {}
        
        # Calculate SerpAPI cost
        if serpapi_searches > 0:
            serpapi_cost = self._calculate_serpapi_cost(serpapi_searches)
            service_costs.append(serpapi_cost)
            
            # Check if we need to recommend tier upgrade
            current_limit = self.SERPAPI_TIERS[self.current_serpapi_tier]['monthly_searches']
            if serpapi_searches > current_limit:
                next_tier = self._recommend_serpapi_tier(serpapi_searches)
                warnings.append(
                    f"WARNING: {serpapi_searches} searches exceeds {self.current_serpapi_tier.value} tier limit ({current_limit})"
                )
                tier_recommendations['serpapi'] = next_tier.value
        
        # Calculate OpenAI costs
        if openai_calls:
            for call in openai_calls:
                openai_cost = self._calculate_openai_cost(
                    model=call.get('model', ModelType.GPT_4O_MINI),
                    input_tokens=call.get('input_tokens', 0),
                    output_tokens=call.get('output_tokens', 0)
                )
                service_costs.append(openai_cost)
        
        # Calculate Firestore costs
        if firestore_reads > 0 or firestore_writes > 0:
            firestore_cost = self._calculate_firestore_cost(firestore_reads, firestore_writes)
            service_costs.append(firestore_cost)
        
        # Calculate total
        total_usd = sum(sc.total_cost for sc in service_costs)
        
        return MissionCost(
            total_usd=total_usd,
            service_costs=service_costs,
            tier_recommendations=tier_recommendations,
            warnings=warnings
        )
    
    def _calculate_serpapi_cost(self, num_searches: int) -> ServiceCost:
        """Calculate SerpAPI cost based on current tier."""
        tier_info = self.SERPAPI_TIERS[self.current_serpapi_tier]
        monthly_cost = tier_info['monthly_cost']
        monthly_searches = tier_info['monthly_searches']
        
        if monthly_searches == 0:  # Free tier has no searches
            unit_cost = 0.0
            total_cost = 0.0
        else:
            unit_cost = monthly_cost / monthly_searches
            total_cost = num_searches * unit_cost
        
        return ServiceCost(
            service="serpapi",
            operation_count=num_searches,
            unit_cost=unit_cost,
            total_cost=total_cost,
            tier=self.current_serpapi_tier.value,
            details={
                'tier_limit': monthly_searches,
                'tier_monthly_cost': monthly_cost
            }
        )
    
    def _calculate_openai_cost(
        self,
        model: ModelType,
        input_tokens: int,
        output_tokens: int
    ) -> ServiceCost:
        """Calculate OpenAI API cost for a single call."""
        pricing = self.OPENAI_PRICING[model]
        
        # Convert from per-1M-tokens to per-token
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        total_cost = input_cost + output_cost
        
        return ServiceCost(
            service="openai",
            operation_count=input_tokens + output_tokens,
            unit_cost=total_cost / (input_tokens + output_tokens) if (input_tokens + output_tokens) > 0 else 0,
            total_cost=total_cost,
            tier=model.value,
            details={
                'model': model.value,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'input_cost': round(input_cost, 6),
                'output_cost': round(output_cost, 6)
            }
        )
    
    def _calculate_firestore_cost(self, reads: int, writes: int) -> ServiceCost:
        """Calculate Firestore operation costs."""
        read_cost = (reads / 100_000) * self.FIRESTORE_PRICING['read_per_100k']
        write_cost = (writes / 100_000) * self.FIRESTORE_PRICING['write_per_100k']
        total_cost = read_cost + write_cost
        
        return ServiceCost(
            service="firestore",
            operation_count=reads + writes,
            unit_cost=total_cost / (reads + writes) if (reads + writes) > 0 else 0,
            total_cost=total_cost,
            details={
                'reads': reads,
                'writes': writes,
                'read_cost': round(read_cost, 6),
                'write_cost': round(write_cost, 6)
            }
        )
    
    def _recommend_serpapi_tier(self, required_searches: int) -> ServiceTier:
        """Recommend appropriate SerpAPI tier for search volume."""
        for tier in [ServiceTier.FREE, ServiceTier.STARTER, ServiceTier.GROWTH, ServiceTier.SCALE]:
            tier_info = self.SERPAPI_TIERS[tier]
            if required_searches <= tier_info['monthly_searches']:
                return tier
        
        # If exceeds all tiers, recommend Scale
        return ServiceTier.SCALE
    
    def estimate_tool_cost(self, tool_name: str, tool_params: Dict[str, Any]) -> MissionCost:
        """
        Estimate cost for a specific tool execution.
        
        Args:
            tool_name: Name of the tool (e.g., "web_search", "llm_call", "firestore_read")
            tool_params: Tool-specific parameters
            
        Returns:
            MissionCost: Cost estimate for this tool
        """
        # Map tool names to cost estimation
        tool_cost_map = {
            'web_search': lambda p: self.estimate_mission_cost(serpapi_searches=p.get('queries', 1)),
            'serp_search': lambda p: self.estimate_mission_cost(serpapi_searches=p.get('queries', 1)),
            'llm_call': lambda p: self.estimate_mission_cost(openai_calls=[{
                'model': ModelType[p.get('model', 'GPT_4O_MINI').upper().replace('-', '_')],
                'input_tokens': p.get('input_tokens', 1000),
                'output_tokens': p.get('output_tokens', 500)
            }]),
            'firestore_read': lambda p: self.estimate_mission_cost(
                firestore_reads=p.get('count', 1)
            ),
            'firestore_write': lambda p: self.estimate_mission_cost(
                firestore_writes=p.get('count', 1)
            ),
        }
        
        estimator = tool_cost_map.get(tool_name.lower())
        if estimator:
            return estimator(tool_params)
        else:
            logger.warning(f"No cost estimator for tool: {tool_name}")
            return MissionCost(total_usd=0.0, service_costs=[])
