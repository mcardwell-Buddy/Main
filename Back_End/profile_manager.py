import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

BUDDY_ROOT = Path(__file__).resolve().parents[1]
PROFILE_FILE = BUDDY_ROOT / "user_profile.json"


def load_profile() -> Dict[str, Any]:
    """Load user profile data from local file or environment variables."""
    profile: Dict[str, Any] = {}

    # 1) Load from local profile file if it exists
    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                profile = json.load(f)
        except Exception:
            profile = {}

    # 2) Environment overrides (optional)
    # Example keys: USER_FULL_NAME, USER_EMAIL, USER_PHONE_MOBILE, USER_PHONE_OFFICE
    env_full_name = os.getenv("USER_FULL_NAME")
    env_email = os.getenv("USER_EMAIL")
    env_phone_mobile = os.getenv("USER_PHONE_MOBILE")
    env_phone_office = os.getenv("USER_PHONE_OFFICE")

    if env_full_name:
        profile["full_name"] = env_full_name
    if env_email:
        profile["email"] = env_email

    if env_phone_mobile or env_phone_office:
        profile.setdefault("phones", {})
        if env_phone_mobile:
            profile["phones"]["mobile"] = env_phone_mobile
        if env_phone_office:
            profile["phones"]["office"] = env_phone_office

    return profile


def has_profile() -> bool:
    """Check whether any profile data is available."""
    profile = load_profile()
    return bool(profile)


def get_profile_field(field: str, default: Optional[Any] = None) -> Any:
    """Get a single field from the profile using a dotted path."""
    profile = load_profile()
    current: Any = profile
    for part in field.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current

