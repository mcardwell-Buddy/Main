"""
Personality Engine - Tone and style modulation for responses.

Phase 8: Applies a consistent, natural tone without altering content meaning.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from backend.response_engine.types import Response


@dataclass
class PersonalityProfile:
    """Defines a response tone profile."""
    name: str
    greeting: Optional[str] = None
    closing: Optional[str] = None
    style: str = "neutral"  # neutral, friendly, concise, professional


class PersonalityEngine:
    """Applies tone and style to Response content."""

    def __init__(self, profile: Optional[PersonalityProfile] = None):
        self.profile = profile or PersonalityProfile(name="default", style="neutral")

    def apply(self, response: Response) -> Response:
        """
        Apply personality to a response in-place and return it.
        """
        if response.primary_content:
            response.primary_content = self._apply_tone(response.primary_content)
        return response

    def _apply_tone(self, text: str) -> str:
        """
        Apply tone based on profile while preserving content meaning.
        """
        if self.profile.style == "concise":
            return text.strip()

        if self.profile.style == "friendly":
            greeting = self.profile.greeting or "Hi!"
            closing = self.profile.closing or "Let me know if you want tweaks."
            return f"{greeting} {text.strip()} {closing}".strip()

        if self.profile.style == "professional":
            greeting = self.profile.greeting or "Hello."
            closing = self.profile.closing or "Please let me know if you'd like adjustments."
            return f"{greeting} {text.strip()} {closing}".strip()

        return text.strip()


class PersonalityRegistry:
    """Registry for reusable personality profiles."""

    def __init__(self):
        self._profiles: Dict[str, PersonalityProfile] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        self.register(PersonalityProfile(name="default", style="neutral"))
        self.register(PersonalityProfile(name="friendly", style="friendly", greeting="Hey!", closing="Want me to refine it?"))
        self.register(PersonalityProfile(name="professional", style="professional", greeting="Hello.", closing="Please advise if revisions are needed."))
        self.register(PersonalityProfile(name="concise", style="concise"))

    def register(self, profile: PersonalityProfile) -> None:
        self._profiles[profile.name] = profile

    def get(self, name: str) -> PersonalityProfile:
        return self._profiles.get(name, self._profiles["default"])
