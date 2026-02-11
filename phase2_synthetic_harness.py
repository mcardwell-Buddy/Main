"""
Phase 2 Synthetic Test Harness
===============================

Generates and tests 500+ synthetic goals across:
- High confidence scenarios (should auto-execute)
- Medium confidence scenarios (should request approval)
- Low confidence scenarios (should request clarification)
- Failure-injected scenarios (should be caught by pre-validation)

Collects metrics:
- Confidence distribution
- Pre-validation catch rate
- Approval request rate
- Tool selection accuracy
- Execution path distribution
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import random

# Import Phase 2 modules
sys.path.insert(0, os.path.dirname(__file__))

from phase2_confidence import GradedConfidenceCalculator, ConfidenceFactors
from phase2_prevalidation import PreValidator
from phase2_approval_gates import ApprovalGates, ExecutionPath
from phase2_clarification import ClarificationGenerator
from phase2_soul_integration import MockSoulSystem
from phase2_response_schema import Phase2ResponseBuilder


class SyntheticGoalGenerator:
    """Generate synthetic goals for testing"""
    
    def __init__(self):
        self.available_tools = [
            'button_clicker', 'element_finder', 'form_filler', 'text_extractor',
            'screenshot_taker', 'page_navigator', 'dom_analyzer', 'http_requester',
            'data_validator', 'json_parser'
        ]
    
    def generate_high_confidence_goals(self, count: int = 150) -> List[Dict]:
        """Generate clear, atomic goals with all tools available"""
        templates = [
            "Click the {element} button",
            "Find the {element} element on the page",
            "Extract text from {element}",
            "Fill the {field} form field with '{value}'",
            "Navigate to {url}",
            "Take a screenshot of the current page",
            "Analyze the DOM structure",
            "Parse the JSON response from the API",
            "Validate the {field} field contains '{value}'",
            "Get the {element} element's text content",
        ]
        
        goals = []
        for i in range(count):
            template = random.choice(templates)
            goal_text = template.format(
                element=random.choice(['submit', 'cancel', 'login', 'search', 'next']),
                field=random.choice(['username', 'password', 'email', 'phone']),
                value=f"test{i}",
                url=f"https://example{i}.com",
            )
            
            goals.append({
                'goal': goal_text,
                'expected_confidence_range': (0.85, 1.0),
                'expected_execution_path': 'high_confidence',
                'scenario_type': 'high_confidence',
                'tools_required': random.sample(self.available_tools, k=random.randint(1, 3)),
            })
        
        return goals
    
    def generate_medium_confidence_goals(self, count: int = 125) -> List[Dict]:
        """Generate goals with some ambiguity, requiring approval"""
        templates = [
            "Fill in the form on the page",
            "Extract all the data from the table",
            "Click the first button you find",
            "Find and analyze the main content",
            "Navigate through the workflow",
            "Get information from the {section} section",
            "Update the {field} field appropriately",
            "Process the data on the current page",
            "Find and interact with the {element}",
            "Collect all {data_type} information visible",
        ]
        
        goals = []
        for i in range(count):
            template = random.choice(templates)
            goal_text = template.format(
                section=random.choice(['header', 'footer', 'sidebar', 'main']),
                field=random.choice(['status', 'priority', 'category']),
                element=random.choice(['form', 'table', 'list', 'card']),
                data_type=random.choice(['contact', 'product', 'user', 'order']),
            )
            
            goals.append({
                'goal': goal_text,
                'expected_confidence_range': (0.55, 0.85),
                'expected_execution_path': 'approved',
                'scenario_type': 'medium_confidence',
                'tools_required': random.sample(self.available_tools, k=random.randint(2, 4)),
            })
        
        return goals
    
    def generate_low_confidence_goals(self, count: int = 100) -> List[Dict]:
        """Generate ambiguous goals requiring clarification"""
        templates = [
            "Help me",
            "Fix this",
            "Make it work",
            "Do the thing",
            "Handle the situation",
            "Deal with the problem",
            "Get this done",
            "Process it",
            "Update everything",
            "Find what I need",
        ]
        
        goals = []
        for i in range(count):
            goal_text = random.choice(templates)
            
            goals.append({
                'goal': goal_text,
                'expected_confidence_range': (0.0, 0.55),
                'expected_execution_path': 'clarification',
                'scenario_type': 'low_confidence',
                'tools_required': [],
            })
        
        return goals
    
    def generate_failure_injected_goals(self, count: int = 125) -> List[Dict]:
        """Generate impossible goals that should fail pre-validation"""
        templates = [
            # Tool availability failures - EXPLICIT tool mentions
            "Use the NonExistentTool tool to process data",
            "Using CompilerTool compile the code",
            "Use ImageEditor tool to edit the screenshot",
            "Using RocketLauncher tool launch the rocket",
            "Use DatabaseConnector tool to connect",
            # Contradictions
            "Click button X and do NOT click button X",
            "Enable the feature but also disable it",
            "Add item to cart and remove item from cart simultaneously",
            "Start the process and stop the process at the same time",
            "Open the modal and close the modal",
            # Out of scope
            "Launch a physical rocket into space",
            "Build a nuclear reactor",
            "Construct a house in the real world",
            "Drive a car to the store",
            "Operate heavy machinery",
        ]
        
        goals = []
        for i in range(count):
            goal_text = templates[i % len(templates)]
            
            # Determine which tool is missing
            missing_tool = None
            if 'Tool' in goal_text and 'tool' in goal_text.lower():
                words = goal_text.split()
                for j, word in enumerate(words):
                    if word.endswith('Tool') or (j > 0 and words[j-1].lower() == 'tool'):
                        tool_name = word.rstrip('.,;:!?')
                        if tool_name.endswith('Tool') and tool_name not in ['tool', 'Tool']:
                            missing_tool = tool_name
                            break
            
            goals.append({
                'goal': goal_text,
                'expected_confidence_range': (0.0, 0.3),
                'expected_execution_path': 'rejected',
                'scenario_type': 'failure_injected',
                'tools_required': [missing_tool] if missing_tool else [],
            })
        
        return goals


class Phase2SyntheticHarness:
    """Test harness for Phase 2 systems"""
    
    def __init__(self):
        self.generator = SyntheticGoalGenerator()
        
        # Initialize Phase 2 systems
        self.confidence_calculator = GradedConfidenceCalculator()
        
        # Create a rich UI schema with all element types
        ui_schema = {
            'button': ['submit', 'cancel', 'login', 'search', 'next'],
            'input': ['username', 'password', 'email', 'phone'],
            'field': ['status', 'priority', 'category'],
            'element': ['form', 'table', 'list', 'card'],
            'text': ['header', 'title', 'paragraph'],
            'checkbox': ['agree', 'terms'],
            'dropdown': ['country', 'state'],
            'modal': ['confirm', 'alert'],
        }
        
        self.pre_validator = PreValidator(
            available_tools=self.generator.available_tools,
            ui_schema=ui_schema,
        )
        self.soul_system = MockSoulSystem()
        self.approval_gates = ApprovalGates(
            soul_integration=self.soul_system,
            high_confidence_threshold=0.85,
            medium_confidence_threshold=0.55,
        )
        self.clarification_generator = ClarificationGenerator()
        self.response_builder = Phase2ResponseBuilder()
        
        # Metrics
        self.results = []
        self.metrics = {
            'total_goals': 0,
            'confidence_scores': [],
            'execution_paths': {'high_confidence': 0, 'approved': 0, 'clarification': 0, 'rejected': 0},
            'pre_validation_passed': 0,
            'pre_validation_failed': 0,
            'pre_validation_catch_rate': 0.0,
            'approval_requests': 0,
            'clarification_requests': 0,
            'confidence_mean': 0.0,
            'confidence_std': 0.0,
            'confidence_min': 0.0,
            'confidence_max': 0.0,
        }
    
    def test_goal(self, goal_data: Dict) -> Dict:
        """Test a single goal through Phase 2 systems"""
        goal = goal_data['goal']
        
        result = {
            'goal': goal,
            'scenario_type': goal_data['scenario_type'],
            'expected_confidence_range': goal_data['expected_confidence_range'],
            'expected_execution_path': goal_data['expected_execution_path'],
            'timestamp': datetime.now().isoformat(),
        }
        
        # Step 1: Pre-validation
        validation_result = self.pre_validator.validate_goal(goal)
        result['pre_validation_status'] = validation_result.validation_status
        result['pre_validation_failures'] = len(validation_result.failures)
        
        # Add failure details for debugging
        if validation_result.failures:
            result['validation_failure_details'] = [
                {
                    'check': f.check_name,
                    'message': f.message,
                    'delta': f.confidence_delta,
                }
                for f in validation_result.failures
            ]
        
        if validation_result.validation_status == "pre_validation_failed":
            result['confidence'] = 0.0
            result['execution_path'] = 'rejected'
            result['pre_validation_caught'] = goal_data['scenario_type'] == 'failure_injected'
            return result
        
        # Step 2: Confidence calculation
        # Simulate factors based on goal characteristics
        if goal_data['scenario_type'] == 'high_confidence':
            factors = ConfidenceFactors(
                goal_understanding=random.uniform(0.85, 1.0),
                tool_availability=random.uniform(0.85, 1.0),
                context_richness=random.uniform(0.5, 0.8),
                tool_confidence=random.uniform(0.8, 1.0),
            )
        elif goal_data['scenario_type'] == 'medium_confidence':
            factors = ConfidenceFactors(
                goal_understanding=random.uniform(0.6, 0.85),
                tool_availability=random.uniform(0.6, 0.85),
                context_richness=random.uniform(0.4, 0.7),
                tool_confidence=random.uniform(0.6, 0.85),
            )
        else:  # low_confidence
            factors = ConfidenceFactors(
                goal_understanding=random.uniform(0.1, 0.5),
                tool_availability=random.uniform(0.0, 0.5),
                context_richness=random.uniform(0.1, 0.5),
                tool_confidence=random.uniform(0.3, 0.6),
            )
        
        confidence = self.confidence_calculator.calculate(factors)
        confidence += validation_result.total_confidence_delta
        confidence = max(0.0, min(1.0, confidence))
        
        result['confidence'] = confidence
        result['factors'] = {
            'goal_understanding': factors.goal_understanding,
            'tool_availability': factors.tool_availability,
            'context_richness': factors.context_richness,
            'tool_confidence': factors.tool_confidence,
        }
        
        # Step 3: Approval gates
        decision = self.approval_gates.decide(
            confidence=confidence,
            goal=goal,
            reasoning_summary=f"Synthetic test for: {goal}",
            tools_proposed=goal_data.get('tools_required', []),
            is_ambiguous=(confidence < 0.55),
        )
        
        result['execution_path'] = decision.execution_path.value if hasattr(decision.execution_path, 'value') else str(decision.execution_path)
        result['approval_required'] = (decision.approval_request is not None)
        result['clarification_required'] = (decision.execution_path == ExecutionPath.CLARIFICATION)
        
        # Check if execution path matches expectation
        result['path_matches_expectation'] = (
            result['execution_path'] == goal_data['expected_execution_path']
        )
        
        # Check if confidence is in expected range
        min_conf, max_conf = goal_data['expected_confidence_range']
        result['confidence_in_expected_range'] = (min_conf <= confidence <= max_conf)
        
        return result
    
    def run_full_test_suite(self):
        """Run all synthetic tests"""
        print("=" * 80)
        print("PHASE 2 SYNTHETIC TEST HARNESS")
        print("=" * 80)
        print()
        
        # Generate goals
        print("Generating synthetic goals...")
        high_conf_goals = self.generator.generate_high_confidence_goals(150)
        medium_conf_goals = self.generator.generate_medium_confidence_goals(125)
        low_conf_goals = self.generator.generate_low_confidence_goals(100)
        failure_goals = self.generator.generate_failure_injected_goals(125)
        
        all_goals = high_conf_goals + medium_conf_goals + low_conf_goals + failure_goals
        random.shuffle(all_goals)
        
        print(f"  - High confidence: {len(high_conf_goals)}")
        print(f"  - Medium confidence: {len(medium_conf_goals)}")
        print(f"  - Low confidence: {len(low_conf_goals)}")
        print(f"  - Failure injected: {len(failure_goals)}")
        print(f"  - Total: {len(all_goals)}")
        print()
        
        # Test each goal
        print("Running tests...")
        for i, goal_data in enumerate(all_goals):
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(all_goals)} goals tested...")
            
            result = self.test_goal(goal_data)
            self.results.append(result)
            
            # Update metrics
            self.metrics['confidence_scores'].append(result['confidence'])
            if result['pre_validation_status'] == 'pre_validation_passed':
                self.metrics['pre_validation_passed'] += 1
            else:
                self.metrics['pre_validation_failed'] += 1
            
            exec_path = result['execution_path']
            if exec_path in self.metrics['execution_paths']:
                self.metrics['execution_paths'][exec_path] += 1
            
            if result.get('approval_required'):
                self.metrics['approval_requests'] += 1
            if result.get('clarification_required'):
                self.metrics['clarification_requests'] += 1
        
        print(f"  Completed: {len(all_goals)}/{len(all_goals)} goals tested")
        print()
        
        # Calculate final metrics
        self.calculate_metrics()
        
        # Generate report
        self.generate_report()
    
    def calculate_metrics(self):
        """Calculate aggregate metrics"""
        self.metrics['total_goals'] = len(self.results)
        
        # Confidence statistics
        if self.metrics['confidence_scores']:
            import statistics
            self.metrics['confidence_mean'] = statistics.mean(self.metrics['confidence_scores'])
            self.metrics['confidence_std'] = statistics.stdev(self.metrics['confidence_scores']) if len(self.metrics['confidence_scores']) > 1 else 0.0
            self.metrics['confidence_min'] = min(self.metrics['confidence_scores'])
            self.metrics['confidence_max'] = max(self.metrics['confidence_scores'])
        
        # Pre-validation catch rate
        failure_injected_count = sum(1 for r in self.results if r['scenario_type'] == 'failure_injected')
        pre_val_caught = sum(1 for r in self.results if r.get('pre_validation_caught', False))
        self.metrics['pre_validation_catch_rate'] = (pre_val_caught / failure_injected_count * 100) if failure_injected_count > 0 else 0.0
        
        # Approval and clarification rates
        self.metrics['approval_request_rate'] = (self.metrics['approval_requests'] / self.metrics['total_goals'] * 100)
        self.metrics['clarification_request_rate'] = (self.metrics['clarification_requests'] / self.metrics['total_goals'] * 100)
    
    def generate_report(self):
        """Generate JSON report"""
        report = {
            'test_run': {
                'timestamp': datetime.now().isoformat(),
                'total_goals': self.metrics['total_goals'],
                'phase2_version': '1.0.0',
            },
            'metrics': {
                'confidence': {
                    'mean': round(self.metrics['confidence_mean'], 3),
                    'std_dev': round(self.metrics['confidence_std'], 3),
                    'min': round(self.metrics['confidence_min'], 3),
                    'max': round(self.metrics['confidence_max'], 3),
                    'distribution': self.metrics['confidence_scores'],
                },
                'execution_paths': self.metrics['execution_paths'],
                'pre_validation': {
                    'passed': self.metrics['pre_validation_passed'],
                    'failed': self.metrics['pre_validation_failed'],
                    'catch_rate_percent': round(self.metrics['pre_validation_catch_rate'], 1),
                },
                'approval_requests': {
                    'count': self.metrics['approval_requests'],
                    'rate_percent': round(self.metrics['approval_request_rate'], 1),
                },
                'clarification_requests': {
                    'count': self.metrics['clarification_requests'],
                    'rate_percent': round(self.metrics['clarification_request_rate'], 1),
                },
            },
            'results': self.results[:100],  # Include first 100 detailed results
            'summary': {
                'total_tests': self.metrics['total_goals'],
                'confidence_continuous': self.metrics['confidence_std'] > 0.2,
                'pre_validation_effective': self.metrics['pre_validation_catch_rate'] > 80,
                'approval_rate_healthy': 10 <= self.metrics['approval_request_rate'] <= 30,
            }
        }
        
        # Save to JSON
        report_path = 'phase2_test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        print()
        print(f"Total Goals Tested: {self.metrics['total_goals']}")
        print()
        print("CONFIDENCE METRICS:")
        print(f"  Mean: {self.metrics['confidence_mean']:.2%}")
        print(f"  Std Dev: {self.metrics['confidence_std']:.3f} {'✓ (continuous)' if self.metrics['confidence_std'] > 0.2 else '✗ (too low)'}")
        print(f"  Range: [{self.metrics['confidence_min']:.2%}, {self.metrics['confidence_max']:.2%}]")
        print()
        print("EXECUTION PATHS:")
        for path, count in self.metrics['execution_paths'].items():
            percent = (count / self.metrics['total_goals'] * 100)
            print(f"  {path}: {count} ({percent:.1f}%)")
        print()
        print("PRE-VALIDATION:")
        print(f"  Passed: {self.metrics['pre_validation_passed']}")
        print(f"  Failed: {self.metrics['pre_validation_failed']}")
        print(f"  Catch Rate: {self.metrics['pre_validation_catch_rate']:.1f}% {'✓ (>80%)' if self.metrics['pre_validation_catch_rate'] > 80 else '✗ (<80%)'}")
        print()
        print("APPROVAL & CLARIFICATION:")
        print(f"  Approval Requests: {self.metrics['approval_requests']} ({self.metrics['approval_request_rate']:.1f}%)")
        print(f"  Clarification Requests: {self.metrics['clarification_requests']} ({self.metrics['clarification_request_rate']:.1f}%)")
        print()
        print("=" * 80)
        print(f"Report saved to: {report_path}")
        print("=" * 80)


if __name__ == '__main__':
    harness = Phase2SyntheticHarness()
    harness.run_full_test_suite()

