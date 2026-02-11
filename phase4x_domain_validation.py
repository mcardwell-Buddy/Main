"""
Phase 4x Step 3: Forecast Domain Contract Validation

Validates forecast domain contracts:
1. Load contracts from JSON
2. Validate schema correctness
3. Print domain summaries
4. Check hard constraints enforcement
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.learning.forecast_domain_contract import (
    DomainContract,
    load_domain_contracts,
    validate_all_contracts
)


def print_contract_summary(contract: DomainContract) -> None:
    """Print human-readable summary of a domain contract."""
    print(f"Domain: {contract.domain_name}")
    print(f"  Description: {contract.description}")
    print(f"  Confidence Cap: {contract.confidence_cap}")
    print(f"  Evaluation Delay: {contract.evaluation_delay_hours} hours")
    print(f"  Allowed Signal Layers: {', '.join(contract.allowed_signal_layers)}")
    print(f"  Forbidden Actions ({len(contract.forbidden_actions)}):")
    for action in contract.forbidden_actions:
        print(f"    - {action}")
    print()


def check_hard_constraints(contracts: List[DomainContract]) -> Dict[str, List[str]]:
    """
    Check that all contracts enforce required hard constraints.
    
    Returns:
        Dictionary of violations by domain name
    """
    required_forbidden = {
        "execute_trade",
        "modify_production_code",
        "send_external_request",
        "autonomous_decision"
    }
    
    violations = {}
    
    for contract in contracts:
        missing = []
        for action in required_forbidden:
            if action not in contract.forbidden_actions:
                missing.append(action)
        
        if missing:
            violations[contract.domain_name] = missing
    
    return violations


def validate_domain_contracts():
    """Run validation checks."""
    print("Phase 4x Step 3: Forecast Domain Contract Validation")
    print("=" * 60)
    print()
    
    # Load contracts
    contracts_path = Path(__file__).parent / "outputs" / "phase25" / "forecast_domains.json"
    
    if not contracts_path.exists():
        print(f"✗ Contracts file not found: {contracts_path}")
        return 1
    
    print(f"Loading contracts from: {contracts_path}")
    contracts = load_domain_contracts(contracts_path)
    print(f"Loaded {len(contracts)} domain contracts")
    print()
    
    # Validate all contracts
    print("Validating Contracts")
    print("-" * 60)
    validation_summary = validate_all_contracts(contracts)
    
    print(f"Total contracts: {validation_summary['total_contracts']}")
    print(f"Valid contracts: {validation_summary['valid_contracts']}")
    print(f"Invalid contracts: {validation_summary['invalid_contracts']}")
    print()
    
    if validation_summary["invalid_contracts"] > 0:
        print("Validation Errors:")
        for domain_name, errors in validation_summary["errors_by_domain"].items():
            print(f"  {domain_name}:")
            for error in errors:
                print(f"    - {error}")
        print()
    
    # Check hard constraints
    print("Hard Constraints Check")
    print("-" * 60)
    violations = check_hard_constraints(contracts)
    
    if violations:
        print("✗ Hard constraint violations found:")
        for domain_name, missing_actions in violations.items():
            print(f"  {domain_name}: Missing {missing_actions}")
        print()
    else:
        print("✓ All contracts enforce required hard constraints:")
        print("  - execute_trade")
        print("  - modify_production_code")
        print("  - send_external_request")
        print("  - autonomous_decision")
        print()
    
    # Print domain summaries
    print("Domain Summaries")
    print("-" * 60)
    for contract in contracts:
        print_contract_summary(contract)
    
    # Validation checks
    print("Validation Checks")
    print("-" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Contracts loaded
    checks_total += 1
    if len(contracts) > 0:
        print("✓ Contracts loaded successfully")
        checks_passed += 1
    else:
        print("✗ No contracts loaded")
    
    # Check 2: Expected number of domains
    checks_total += 1
    if len(contracts) == 4:
        print("✓ Expected 4 domains present")
        checks_passed += 1
    else:
        print(f"✗ Expected 4 domains, got {len(contracts)}")
    
    # Check 3: All contracts valid
    checks_total += 1
    if validation_summary["invalid_contracts"] == 0:
        print("✓ All contracts passed validation")
        checks_passed += 1
    else:
        print(f"✗ {validation_summary['invalid_contracts']} contracts failed validation")
    
    # Check 4: Hard constraints enforced
    checks_total += 1
    if not violations:
        print("✓ All contracts enforce hard constraints")
        checks_passed += 1
    else:
        print(f"✗ {len(violations)} contracts missing hard constraints")
    
    # Check 5: Confidence caps reasonable
    checks_total += 1
    all_caps_reasonable = all(c.confidence_cap <= 0.7 for c in contracts)
    if all_caps_reasonable:
        print("✓ All confidence caps <= 0.7 (conservative)")
        checks_passed += 1
    else:
        print("✗ Some confidence caps too high")
    
    # Check 6: Domain names unique
    checks_total += 1
    domain_names = [c.domain_name for c in contracts]
    if len(domain_names) == len(set(domain_names)):
        print("✓ All domain names unique")
        checks_passed += 1
    else:
        print("✗ Duplicate domain names found")
    
    # Check 7: Required domains present
    checks_total += 1
    required_domains = {
        "internal_system_health",
        "business_opportunity",
        "financial_markets",
        "environmental"
    }
    present_domains = {c.domain_name for c in contracts}
    if required_domains.issubset(present_domains):
        print("✓ All required domains present")
        checks_passed += 1
    else:
        missing = required_domains - present_domains
        print(f"✗ Missing required domains: {missing}")
    
    print()
    print(f"Validation Result: {checks_passed}/{checks_total} checks passed")
    print()
    
    if checks_passed == checks_total:
        print("✓ Phase 4x Step 3 validation PASSED")
        return 0
    else:
        print("✗ Phase 4x Step 3 validation FAILED")
        return 1


if __name__ == "__main__":
    exit_code = validate_domain_contracts()
    sys.exit(exit_code)

