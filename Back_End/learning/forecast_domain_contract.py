"""
Phase 4x Step 3: Forecast Domain Contract

Defines explicit constraints for any future forecasting domain.
Hard constraints:
- NO predictions
- NO autonomy
- NO external APIs
- NO execution changes

Pure configuration + validation only.
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Optional
from pathlib import Path


@dataclass
class DomainContract:
    """
    Contract defining constraints for a forecasting domain.
    
    Attributes:
        domain_name: Unique identifier for the domain
        allowed_signal_layers: Which signal layers can be used for this domain
        confidence_cap: Maximum confidence value (0.0-1.0) for forecasts
        evaluation_delay_hours: How long to wait before evaluating forecast accuracy
        forbidden_actions: List of explicitly forbidden actions
        description: Human-readable description of the domain
    """
    domain_name: str
    allowed_signal_layers: List[str]
    confidence_cap: float
    evaluation_delay_hours: int
    forbidden_actions: List[str]
    description: str
    
    def validate(self) -> List[str]:
        """
        Validate contract constraints.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate domain_name
        if not self.domain_name:
            errors.append("domain_name cannot be empty")
        
        if " " in self.domain_name:
            errors.append("domain_name cannot contain spaces")
        
        # Validate allowed_signal_layers
        if not self.allowed_signal_layers:
            errors.append("allowed_signal_layers cannot be empty")
        
        valid_layers = {"selector", "intent", "mission", "opportunity", "goal", "program", "temporal", "aggregate"}
        for layer in self.allowed_signal_layers:
            if layer not in valid_layers:
                errors.append(f"Invalid signal layer: {layer}")
        
        # Validate confidence_cap
        if not 0.0 <= self.confidence_cap <= 1.0:
            errors.append(f"confidence_cap must be between 0.0 and 1.0, got {self.confidence_cap}")
        
        # Validate evaluation_delay_hours
        if self.evaluation_delay_hours < 0:
            errors.append(f"evaluation_delay_hours must be non-negative, got {self.evaluation_delay_hours}")
        
        # Validate forbidden_actions
        if not self.forbidden_actions:
            errors.append("forbidden_actions cannot be empty (must explicitly list at least one)")
        
        # Hard constraints - these MUST be forbidden
        required_forbidden = {
            "execute_trade",
            "modify_production_code",
            "send_external_request",
            "autonomous_decision"
        }
        
        for action in required_forbidden:
            if action not in self.forbidden_actions:
                errors.append(f"Required forbidden action missing: {action}")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DomainContract':
        """Create from dictionary."""
        return cls(**data)


def create_example_domains() -> List[DomainContract]:
    """
    Create 4 example forecast domain contracts.
    
    These demonstrate different types of forecasting domains with
    appropriate constraints for each.
    """
    
    domains = []
    
    # Domain 1: Internal System Health
    domains.append(DomainContract(
        domain_name="internal_system_health",
        allowed_signal_layers=[
            "selector",
            "intent",
            "mission",
            "temporal",
            "aggregate"
        ],
        confidence_cap=0.7,  # Conservative cap for system predictions
        evaluation_delay_hours=24,  # Check predictions after 1 day
        forbidden_actions=[
            "execute_trade",
            "modify_production_code",
            "send_external_request",
            "autonomous_decision",
            "restart_service",
            "modify_database",
            "change_configuration"
        ],
        description=(
            "Forecasts about Buddy's own internal performance and health. "
            "Includes predictions about selector success rates, mission completion rates, "
            "and potential degradation patterns. Purely observational - no automatic fixes."
        )
    ))
    
    # Domain 2: Business Opportunity
    domains.append(DomainContract(
        domain_name="business_opportunity",
        allowed_signal_layers=[
            "mission",
            "opportunity",
            "goal",
            "program",
            "temporal"
        ],
        confidence_cap=0.5,  # Very conservative for business predictions
        evaluation_delay_hours=168,  # Check after 1 week
        forbidden_actions=[
            "execute_trade",
            "modify_production_code",
            "send_external_request",
            "autonomous_decision",
            "commit_resources",
            "sign_contract",
            "make_investment"
        ],
        description=(
            "Forecasts about potential business opportunities detected during missions. "
            "Could identify patterns in scraped data suggesting market trends or opportunities. "
            "Human review required before any action."
        )
    ))
    
    # Domain 3: Financial Markets
    domains.append(DomainContract(
        domain_name="financial_markets",
        allowed_signal_layers=[
            "temporal",
            "aggregate"
        ],
        confidence_cap=0.3,  # Extremely conservative for financial predictions
        evaluation_delay_hours=72,  # Check after 3 days
        forbidden_actions=[
            "execute_trade",
            "modify_production_code",
            "send_external_request",
            "autonomous_decision",
            "place_order",
            "transfer_funds",
            "access_brokerage_api",
            "recommend_trade",
            "calculate_investment_amount"
        ],
        description=(
            "Forecasts about financial market patterns (if any financial data is encountered). "
            "STRICTLY observational only. NO trading, NO recommendations, NO financial advice. "
            "Exists only to demonstrate contract constraints for high-risk domains."
        )
    ))
    
    # Domain 4: Environmental
    domains.append(DomainContract(
        domain_name="environmental",
        allowed_signal_layers=[
            "temporal",
            "aggregate",
            "mission"
        ],
        confidence_cap=0.6,  # Moderate confidence for pattern detection
        evaluation_delay_hours=720,  # Check after 30 days
        forbidden_actions=[
            "execute_trade",
            "modify_production_code",
            "send_external_request",
            "autonomous_decision",
            "control_physical_device",
            "trigger_alert",
            "modify_sensor_settings"
        ],
        description=(
            "Forecasts about environmental patterns if such data is encountered during missions. "
            "Could detect seasonal patterns, usage patterns, or trends in environmental data. "
            "Read-only observation with long evaluation period."
        )
    ))
    
    return domains


def save_domain_contracts(contracts: List[DomainContract], output_path: Path) -> None:
    """
    Save domain contracts to JSON file.
    
    Args:
        contracts: List of DomainContract objects
        output_path: Path to output JSON file
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dictionaries
    contracts_data = {
        "version": "1.0.0",
        "created_at": "2026-02-07T00:00:00+00:00",
        "description": "Forecast domain contracts defining constraints for future forecasting domains",
        "contracts": [contract.to_dict() for contract in contracts]
    }
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(contracts_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(contracts)} domain contracts to {output_path}")


def load_domain_contracts(contracts_path: Path) -> List[DomainContract]:
    """
    Load domain contracts from JSON file.
    
    Args:
        contracts_path: Path to contracts JSON file
        
    Returns:
        List of DomainContract objects
    """
    if not contracts_path.exists():
        raise FileNotFoundError(f"Contracts file not found: {contracts_path}")
    
    with open(contracts_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    contracts = [DomainContract.from_dict(contract_data) for contract_data in data["contracts"]]
    
    return contracts


def validate_all_contracts(contracts: List[DomainContract]) -> dict:
    """
    Validate all contracts and return summary.
    
    Args:
        contracts: List of DomainContract objects
        
    Returns:
        Validation summary dictionary
    """
    summary = {
        "total_contracts": len(contracts),
        "valid_contracts": 0,
        "invalid_contracts": 0,
        "errors_by_domain": {}
    }
    
    for contract in contracts:
        errors = contract.validate()
        if errors:
            summary["invalid_contracts"] += 1
            summary["errors_by_domain"][contract.domain_name] = errors
        else:
            summary["valid_contracts"] += 1
    
    return summary


if __name__ == "__main__":
    """Generate example domain contracts."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Create example domains
    print("Creating example forecast domain contracts...")
    domains = create_example_domains()
    print(f"Created {len(domains)} domains")
    print()
    
    # Validate all domains
    print("Validating contracts...")
    validation_summary = validate_all_contracts(domains)
    print(f"Valid: {validation_summary['valid_contracts']}/{validation_summary['total_contracts']}")
    
    if validation_summary["invalid_contracts"] > 0:
        print("\nValidation Errors:")
        for domain_name, errors in validation_summary["errors_by_domain"].items():
            print(f"  {domain_name}:")
            for error in errors:
                print(f"    - {error}")
        sys.exit(1)
    
    print()
    
    # Save to file
    output_path = Path(__file__).parent.parent.parent / "outputs" / "phase25" / "forecast_domains.json"
    save_domain_contracts(domains, output_path)
    
    print()
    print("✓ Domain contracts generated and saved")

