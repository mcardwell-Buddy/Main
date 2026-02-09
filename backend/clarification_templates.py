"""
Clarification Templates (Phase 3B)

Pure mapping from ClarificationType to response templates.
No logic, no conditionals. Just structured templates with placeholders.

Placeholders:
- {intent}: The action the user wants to perform (extract, navigate, search)
- {last_source_url}: The URL from the most recent mission
- {reference}: The ambiguous pronoun or reference ("there", "it", "that")
"""

from backend.action_readiness_engine import ClarificationType
from typing import Dict, Optional

# Template for each clarification type
CLARIFICATION_TEMPLATES: Dict[ClarificationType, str] = {
    ClarificationType.MISSING_OBJECT: (
        "I can do that — what exactly would you like me to {intent}?\n\n"
        "For example:\n"
        "• Extract **titles**\n"
        "• Extract **services**\n"
        "• Extract **emails**"
    ),
    
    ClarificationType.MISSING_TARGET: (
        "I know what to {intent}, but I need to know where.\n\n"
        "Should I use:\n"
        "• {last_source_url}\n"
        "• A different website?"
    ),
    
    ClarificationType.MISSING_TARGET_NO_CONTEXT: (
        "I know what to {intent}, but I need to know where.\n\n"
        "Could you provide a website or URL?"
    ),
    
    ClarificationType.AMBIGUOUS_REFERENCE: (
        "When you say \"{reference}\", what are you referring to?\n\n"
        "Please specify the website or data you mean."
    ),
    
    ClarificationType.TOO_VAGUE: (
        "I can help, but I need a bit more detail.\n\n"
        "What kind of information are you looking for?"
    ),
    
    ClarificationType.MULTI_INTENT: (
        "I can help with this, but I want to be sure of the steps.\n\n"
        "Should I:\n"
        "1️⃣ Navigate to a site\n"
        "2️⃣ Then extract data from it\n\n"
        "Reply \"yes\" to proceed, or tell me what to change."
    ),
    
    ClarificationType.INTENT_AMBIGUOUS: (
        "Do you want me to:\n"
        "• **Search** for information\n"
        "• Or **extract** data from a specific website?"
    ),
    
    ClarificationType.CONSTRAINT_UNCLEAR: (
        "How would you like the results formatted or limited?\n\n"
        "For example:\n"
        "• Top 5 results\n"
        "• Summary only\n"
        "• Full list"
    ),
}


def render_clarification(
    clarification_type: Optional[ClarificationType],
    intent: Optional[str] = None,
    last_source_url: Optional[str] = None,
    reference: Optional[str] = None,
) -> str:
    """
    Render a clarification message with the given type and context.
    
    Args:
        clarification_type: The type of clarification needed
        intent: The action the user wants ("extract", "navigate", "search")
        last_source_url: URL from prior mission context
        reference: The ambiguous pronoun ("there", "it", "that")
    
    Returns:
        Rendered clarification message
    """
    if not clarification_type:
        return "I need more information to help you."
    
    # Get the template
    template = CLARIFICATION_TEMPLATES.get(
        clarification_type,
        "I need more information to help you."
    )
    
    # Handle MISSING_TARGET with/without context
    if clarification_type == ClarificationType.MISSING_TARGET:
        if not last_source_url:
            template = CLARIFICATION_TEMPLATES[ClarificationType.MISSING_TARGET_NO_CONTEXT]
    
    # Build placeholder dict
    placeholders = {
        'intent': intent or 'help',
        'last_source_url': last_source_url or 'a website',
        'reference': reference or 'that',
    }
    
    # Render with placeholders
    try:
        return template.format(**placeholders)
    except (KeyError, ValueError):
        # Fallback if placeholder not found
        return template


# Export for use in orchestrator
__all__ = ['ClarificationType', 'render_clarification', 'CLARIFICATION_TEMPLATES']
