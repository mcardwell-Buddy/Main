"""
Buddy Response Engine - Generates rich, interactive responses for mission results.

Phases:
1. Core Response Builder (2-3h) - ResponseType enum, ResponseBuilder, base formatters
2. ContentMetadata Schema (1h) - Track content lifecycle, dependencies, formats
3. Error Recovery (2h) - Graceful fallbacks, retry logic, error context
4. Approval/Confirmation (3-4h) - Interactive prompts, approval workflow
5. Content Formatters (4-5h) - Code, documents, analysis, search results
6. Interactive Components (3-4h) - Buttons, expandable sections, progress
7. Caching Layer (2-3h) - Content caching, regeneration policies
8. Personality Engine (3-4h) - Tone, context awareness, natural language
"""

from Back_End.response_engine.types import ResponseType, ContentMetadata, Response
from Back_End.response_engine.builder import ResponseBuilder
from Back_End.response_engine.formatters import (
    BaseFormatter,
    JSONFormatter,
    MarkdownFormatter,
    HTMLFormatter,
    DocumentFormatter,
    AnalysisFormatter,
    SearchResultsFormatter,
    BusinessPlanFormatter,
)
from Back_End.response_engine.error_recovery import ErrorRecoveryManager, RetryPolicy, RecoveryAction
from Back_End.response_engine.approval import ApprovalManager, ApprovalRequest, ApprovalDecision
from Back_End.response_engine.interactive import (
    InteractiveElement,
    Button,
    Link,
    ExpandableSection,
    ProgressIndicator,
    interactive_to_dict,
)
from Back_End.response_engine.cache import ResponseCache, ResponseCacheManager, CacheEntry
from Back_End.response_engine.personality import PersonalityEngine, PersonalityProfile, PersonalityRegistry

__all__ = [
    'ResponseType',
    'ContentMetadata', 
    'Response',
    'ResponseBuilder',
    'BaseFormatter',
    'JSONFormatter',
    'MarkdownFormatter',
    'HTMLFormatter',
    'DocumentFormatter',
    'AnalysisFormatter',
    'SearchResultsFormatter',
    'BusinessPlanFormatter',
    'ErrorRecoveryManager',
    'RetryPolicy',
    'RecoveryAction',
    'ApprovalManager',
    'ApprovalRequest',
    'ApprovalDecision',
    'InteractiveElement',
    'Button',
    'Link',
    'ExpandableSection',
    'ProgressIndicator',
    'interactive_to_dict',
    'ResponseCache',
    'ResponseCacheManager',
    'CacheEntry',
    'PersonalityEngine',
    'PersonalityProfile',
    'PersonalityRegistry',
]

