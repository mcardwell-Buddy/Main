"""
Phase 2 Soul API Integration - Real Soul Connection
====================================================

Provides safe integration of real Soul API with feature flag control,
fallback to mock, and comprehensive logging.

Features:
- Feature flag: SOUL_REAL_ENABLED environment variable
- Automatic fallback to MockSoulSystem if real Soul fails
- Wrapper around real buddys_soul API
- Full compatibility with Phase 2 SoulInterface
- Comprehensive error handling and logging
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the mock for fallback
from phase2_soul_integration import MockSoulSystem, SoulInterface, ConversationContext


class RealSoulAPIWrapper(SoulInterface):
    """
    Wrapper around real Buddy's Soul API (buddys_soul.py)
    
    Implements the SoulInterface while using real Soul evaluation.
    Falls back to mock if any error occurs.
    """
    
    def __init__(self, use_real_soul: bool = True, verbose: bool = True):
        """
        Initialize Real Soul API wrapper.
        
        Args:
            use_real_soul: Whether to use real Soul API (reads SOUL_REAL_ENABLED env var)
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        
        # Check environment variable
        env_enabled = os.environ.get('SOUL_REAL_ENABLED', 'false').lower() == 'true'
        self.use_real_soul = use_real_soul and env_enabled
        
        # Try to import real Soul API
        self.real_soul = None
        self.soul_available = False
        
        if self.use_real_soul:
            try:
                # Add backend path
                backend_path = Path(__file__).parent / 'backend'
                if backend_path not in sys.path:
                    sys.path.insert(0, str(backend_path))
                
                import buddys_soul
                self.real_soul = buddys_soul
                self.soul_available = True
                
                if self.verbose:
                    logger.info("✅ Real Soul API loaded successfully")
            
            except Exception as e:
                logger.warning(f"⚠️  Failed to load real Soul API: {e}")
                logger.warning("   Falling back to MockSoulSystem")
                self.use_real_soul = False
                self.soul_available = False
        
        # Initialize fallback mock
        self.mock_soul = MockSoulSystem()
        
        # Metrics
        self.stats = {
            'real_soul_calls': 0,
            'mock_soul_calls': 0,
            'errors': 0,
            'evaluations': 0,
        }
    
    def evaluate_alignment(self, text: str) -> Dict[str, Any]:
        """
        Evaluate text alignment with Soul core values.
        
        Uses real Soul API if available, falls back to mock.
        
        Args:
            text: Text to evaluate
        
        Returns:
            {
                'score': float (0.0-1.0),
                'matched_values': List[str],
                'reasons': List[str],
                'source': 'real' | 'mock'
            }
        """
        self.stats['evaluations'] += 1
        
        try:
            if self.soul_available and self.real_soul:
                result = self.real_soul.evaluate_alignment(text)
                result['source'] = 'real'
                self.stats['real_soul_calls'] += 1
                
                if self.verbose:
                    logger.debug(f"Soul alignment evaluation: {text[:50]}... → {result['score']}")
                
                return result
            
            else:
                # Fallback to mock
                result = self.mock_soul.validate_approval_request({
                    'goal': text,
                    'confidence': 0.75
                })
                result['source'] = 'mock'
                self.stats['mock_soul_calls'] += 1
                
                return result
        
        except Exception as e:
            logger.error(f"❌ Error evaluating alignment: {e}")
            self.stats['errors'] += 1
            
            # Emergency fallback
            return {
                'score': 0.5,
                'matched_values': [],
                'reasons': [f'Error: {str(e)}'],
                'source': 'mock_fallback'
            }
    
    def validate_approval_request(
        self,
        approval_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate approval request before sending to user.
        
        Uses real Soul API if available, falls back to mock.
        """
        try:
            if self.soul_available and self.real_soul:
                # Use real Soul to evaluate the goal text
                goal = approval_request.get('goal', '')
                alignment = self.real_soul.evaluate_alignment(goal)
                
                result = {
                    'valid': True,
                    'approved': alignment['score'] >= 0.8,
                    'confidence_score': alignment['score'],
                    'matched_values': alignment.get('matched_values', []),
                    'feedback': f"Soul alignment: {alignment['score']:.2%}",
                    'source': 'real'
                }
                self.stats['real_soul_calls'] += 1
                
                if self.verbose:
                    logger.info(f"✅ Real Soul validation: {goal[:40]}... → approved={result['approved']}")
                
                return result
            
            else:
                # Use mock
                result = self.mock_soul.validate_approval_request(approval_request)
                result['source'] = 'mock'
                self.stats['mock_soul_calls'] += 1
                
                return result
        
        except Exception as e:
            logger.error(f"❌ Error validating approval: {e}")
            self.stats['errors'] += 1
            
            # Fallback: always valid
            return {
                'valid': True,
                'approved': False,
                'feedback': 'Soul validation skipped (error)',
                'source': 'mock_fallback'
            }
    
    def validate_clarification(
        self,
        clarification_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate clarification questions before sending to user.
        """
        try:
            if self.soul_available and self.real_soul:
                # Evaluate clarification alignment
                questions = clarification_request.get('questions', [])
                
                approved_indices = []
                for i, q in enumerate(questions):
                    alignment = self.real_soul.evaluate_alignment(q)
                    if alignment['score'] >= 0.5:
                        approved_indices.append(i)
                
                result = {
                    'valid': len(approved_indices) > 0,
                    'approved_indices': approved_indices,
                    'feedback': f'Soul approved {len(approved_indices)}/{len(questions)} questions',
                    'source': 'real'
                }
                self.stats['real_soul_calls'] += 1
                
                if self.verbose:
                    logger.info(f"✅ Real Soul clarification: {len(approved_indices)}/{len(questions)} approved")
                
                return result
            
            else:
                result = self.mock_soul.validate_clarification(clarification_request)
                result['source'] = 'mock'
                self.stats['mock_soul_calls'] += 1
                
                return result
        
        except Exception as e:
            logger.error(f"❌ Error validating clarification: {e}")
            self.stats['errors'] += 1
            
            return {
                'valid': True,
                'approved_indices': list(range(len(clarification_request.get('questions', [])))),
                'feedback': 'Soul validation skipped (error)',
                'source': 'mock_fallback'
            }
    
    def get_conversation_context(
        self,
        session_id: str,
    ) -> ConversationContext:
        """
        Retrieve prior conversation context.
        
        Real Soul API doesn't provide this, so always use mock.
        """
        return self.mock_soul.get_conversation_context(session_id)
    
    def store_approval_decision(
        self,
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Store approval decision for audit trail.
        
        Real Soul API doesn't provide this, so always use mock.
        """
        return self.mock_soul.store_approval_decision(decision)
    
    def get_soul_values(self) -> Dict[str, List[Dict]]:
        """
        Get Buddy's core Soul values.
        
        Uses real Soul if available, mock otherwise.
        """
        try:
            if self.soul_available and self.real_soul:
                return self.real_soul.get_soul()
            else:
                return self.mock_soul.get_soul()
        except Exception as e:
            logger.error(f"❌ Error getting Soul values: {e}")
            return {"core_values": []}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get integration status and statistics.
        """
        return {
            'real_soul_available': self.soul_available,
            'using_real_soul': self.use_real_soul and self.soul_available,
            'fallback_active': not (self.use_real_soul and self.soul_available),
            'stats': self.stats,
            'soul_environment': os.environ.get('SOUL_REAL_ENABLED', 'not set'),
        }


def get_soul_system(use_real: bool = True, verbose: bool = True) -> SoulInterface:
    """
    Factory function to get appropriate Soul system.
    
    Args:
        use_real: Whether to attempt real Soul API integration
        verbose: Enable logging
    
    Returns:
        SoulInterface implementation (Real or Mock)
    """
    # Check environment variable first
    env_enabled = os.environ.get('SOUL_REAL_ENABLED', 'false').lower() == 'true'
    
    if use_real and env_enabled:
        logger.info("🔗 Initializing Real Soul API integration...")
        return RealSoulAPIWrapper(verbose=verbose)
    else:
        logger.info("🔄 Using MockSoulSystem (Real Soul not enabled)")
        return MockSoulSystem()


# Test function
if __name__ == '__main__':
    # Test without real Soul
    print("Test 1: Using mock (SOUL_REAL_ENABLED not set)")
    soul_mock = get_soul_system(use_real=True, verbose=True)
    if hasattr(soul_mock, 'get_status'):
        print(f"Status: {soul_mock.get_status()}\n")
    else:
        print("Using MockSoulSystem (no status method)\n")
    
    # Test with real Soul
    print("Test 2: Using real Soul API (set SOUL_REAL_ENABLED=true)")
    os.environ['SOUL_REAL_ENABLED'] = 'true'
    soul_real = get_soul_system(use_real=True, verbose=True)
    if hasattr(soul_real, 'get_status'):
        print(f"Status: {soul_real.get_status()}\n")
    
    # Test approval validation
    result = soul_real.validate_approval_request({
        'goal': 'Click the save button',
        'confidence': 0.85
    })
    print(f"Approval validation: {result}")

