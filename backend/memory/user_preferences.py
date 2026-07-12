from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UserPreferences:
    autonomy_mode: str = "autonomous"
    preferred_metric: str | None = None
    preferred_model: str | None = None


user_preferences = UserPreferences()
