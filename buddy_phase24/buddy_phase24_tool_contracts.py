"""
Phase 24: Tool Contracts - Formal contract system for tools

Defines tool contract requirements, risk levels, permissions, and execution constraints.
All tool executions must validate against these contracts before proceeding.
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Set
from enum import Enum
from datetime import datetime, timezone


class RiskLevel(Enum):
    """Tool risk classification"""
    LOW = "LOW"          # Read-only, informational
    MEDIUM = "MEDIUM"    # Reversible, approval needed
    HIGH = "HIGH"        # Irreversible, live approval required


class ExecutionMode(Enum):
    """Valid execution modes"""
    MOCK = "MOCK"              # Simulated execution
    DRY_RUN = "DRY_RUN"        # Safe preview
    LIVE = "LIVE"              # Real execution


@dataclass
class ToolContract:
    """Formal contract for a tool's execution parameters"""
    
    tool_name: str
    risk_level: RiskLevel
    reversible: bool
    required_permissions: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    timeout_seconds: int = 30
    mock_provider_available: bool = True
    description: str = ""
    max_concurrent: int = 1
    requires_approval: bool = False
    
    def __post_init__(self):
        """Validate contract invariants"""
        # HIGH risk tools must be irreversible and require approval
        if self.risk_level == RiskLevel.HIGH and (self.reversible or not self.requires_approval):
            raise ValueError(f"HIGH risk tool '{self.tool_name}' must be irreversible and require approval")
        
        # MEDIUM risk tools should have reasonable defaults
        if self.risk_level == RiskLevel.MEDIUM and self.timeout_seconds < 10:
            self.timeout_seconds = 10
        
        # LOW risk tools can be fast
        if self.risk_level == RiskLevel.LOW and self.timeout_seconds > 5:
            self.timeout_seconds = 5
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['risk_level'] = self.risk_level.value
        data['required_permissions'] = list(self.required_permissions)
        data['dependencies'] = list(self.dependencies)
        return data
    
    def validate_permission(self, permission: str) -> bool:
        """Check if permission is required"""
        return permission in self.required_permissions
    
    def can_execute_in_mode(self, mode: ExecutionMode) -> bool:
        """Check if tool can execute in given mode"""
        if mode == ExecutionMode.MOCK:
            return self.mock_provider_available
        elif mode == ExecutionMode.DRY_RUN:
            return self.mock_provider_available or self.reversible
        elif mode == ExecutionMode.LIVE:
            return True  # Live can execute anything (if approved)
        return False
    
    def requires_escalation_approval(self, current_mode: ExecutionMode, target_mode: ExecutionMode) -> bool:
        """Check if escalation from current to target mode requires approval"""
        # Escalation requires approval for MEDIUM+ risk
        if target_mode == ExecutionMode.LIVE and self.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
            return True
        return False


class ToolContractRegistry:
    """Registry of all tool contracts"""
    
    def __init__(self):
        self.contracts: Dict[str, ToolContract] = {}
        self._initialize_standard_contracts()
    
    def _initialize_standard_contracts(self):
        """Initialize contracts for standard tools"""
        
        # LOW RISK TOOLS (Read-only, informational)
        self.register(ToolContract(
            tool_name="vision_inspect",
            risk_level=RiskLevel.LOW,
            reversible=True,
            description="Inspect page DOM and structure (read-only)",
            timeout_seconds=5,
            mock_provider_available=True
        ))
        
        self.register(ToolContract(
            tool_name="screenshot_capture",
            risk_level=RiskLevel.LOW,
            reversible=True,
            description="Capture screenshot of current page",
            timeout_seconds=3,
            mock_provider_available=True
        ))
        
        self.register(ToolContract(
            tool_name="memory_search",
            risk_level=RiskLevel.LOW,
            reversible=True,
            description="Search agent memory (read-only)",
            timeout_seconds=2,
            mock_provider_available=True
        ))
        
        self.register(ToolContract(
            tool_name="goal_query",
            risk_level=RiskLevel.LOW,
            reversible=True,
            description="Query current goals and status",
            timeout_seconds=1,
            mock_provider_available=True
        ))
        
        # MEDIUM RISK TOOLS (Reversible, approval recommended)
        self.register(ToolContract(
            tool_name="form_fill",
            risk_level=RiskLevel.MEDIUM,
            reversible=True,
            description="Fill form fields (reversible via reload)",
            timeout_seconds=10,
            mock_provider_available=True,
            requires_approval=True
        ))
        
        self.register(ToolContract(
            tool_name="button_click",
            risk_level=RiskLevel.MEDIUM,
            reversible=False,  # Navigation is irreversible
            description="Click button or link",
            timeout_seconds=15,
            mock_provider_available=True,
            requires_approval=True
        ))
        
        self.register(ToolContract(
            tool_name="mployer_search",
            risk_level=RiskLevel.MEDIUM,
            reversible=True,
            description="Search Mployer contacts",
            timeout_seconds=30,
            mock_provider_available=True,
            requires_approval=True,
            required_permissions={"mployer_access"}
        ))
        
        self.register(ToolContract(
            tool_name="ghl_search",
            risk_level=RiskLevel.MEDIUM,
            reversible=True,
            description="Search GoHighLevel contacts",
            timeout_seconds=15,
            mock_provider_available=True,
            requires_approval=True,
            required_permissions={"ghl_access"}
        ))
        
        # HIGH RISK TOOLS (Irreversible, explicit live approval required)
        self.register(ToolContract(
            tool_name="ghl_create_contact",
            risk_level=RiskLevel.HIGH,
            reversible=False,
            description="Create new GHL contact (irreversible)",
            timeout_seconds=20,
            mock_provider_available=True,
            requires_approval=True,
            required_permissions={"ghl_write", "ghl_access"}
        ))
        
        self.register(ToolContract(
            tool_name="mployer_add_contact",
            risk_level=RiskLevel.HIGH,
            reversible=False,
            description="Add contact to Mployer (irreversible)",
            timeout_seconds=25,
            mock_provider_available=True,
            requires_approval=True,
            required_permissions={"mployer_write", "mployer_access"}
        ))
        
        self.register(ToolContract(
            tool_name="msgraph_send_email",
            risk_level=RiskLevel.HIGH,
            reversible=False,
            description="Send email via MS Graph (irreversible)",
            timeout_seconds=20,
            mock_provider_available=True,
            requires_approval=True,
            required_permissions={"email_send"}
        ))
        
        self.register(ToolContract(
            tool_name="web_action_irreversible",
            risk_level=RiskLevel.HIGH,
            reversible=False,
            description="Irreversible web action (submit, delete, etc.)",
            timeout_seconds=30,
            mock_provider_available=True,
            requires_approval=True,
            required_permissions={"web_write"}
        ))
    
    def register(self, contract: ToolContract):
        """Register a tool contract"""
        self.contracts[contract.tool_name] = contract
    
    def get(self, tool_name: str) -> Optional[ToolContract]:
        """Get contract for tool"""
        return self.contracts.get(tool_name)
    
    def validate_tool_request(self, tool_name: str, execution_mode: ExecutionMode) -> tuple[bool, str]:
        """
        Validate if tool can execute in given mode
        
        Returns: (success: bool, message: str)
        """
        contract = self.get(tool_name)
        if not contract:
            return False, f"Tool '{tool_name}' not found in contract registry"
        
        if not contract.can_execute_in_mode(execution_mode):
            return False, f"Tool '{tool_name}' cannot execute in {execution_mode.value} mode"
        
        return True, "Contract validation passed"
    
    def validate_permission(self, tool_name: str, permission: str) -> bool:
        """Check if tool requires specific permission"""
        contract = self.get(tool_name)
        if not contract:
            return False
        return contract.validate_permission(permission)
    
    def get_risk_level(self, tool_name: str) -> Optional[RiskLevel]:
        """Get risk level of tool"""
        contract = self.get(tool_name)
        return contract.risk_level if contract else None
    
    def list_tools_by_risk(self, risk_level: RiskLevel) -> List[str]:
        """List all tools of given risk level"""
        return [name for name, contract in self.contracts.items() 
                if contract.risk_level == risk_level]
    
    def get_statistics(self) -> Dict:
        """Get registry statistics"""
        return {
            "total_tools": len(self.contracts),
            "low_risk": len(self.list_tools_by_risk(RiskLevel.LOW)),
            "medium_risk": len(self.list_tools_by_risk(RiskLevel.MEDIUM)),
            "high_risk": len(self.list_tools_by_risk(RiskLevel.HIGH)),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global registry instance
tool_contract_registry = ToolContractRegistry()
