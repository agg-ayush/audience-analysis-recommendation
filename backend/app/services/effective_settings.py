"""Load effective settings (env defaults merged with DB overrides)."""
import json
import logging

from sqlalchemy.orm import Session

from app.config import get_settings

logger = logging.getLogger(__name__)

# All configurable field names
_SETTINGS_FIELDS = [
    "min_spend", "min_purchases", "min_age_days",
    "winner_threshold", "loser_threshold",
    "improving_slope", "declining_slope", "volatile_cpa_std",
    "roas_weight", "spend_weight", "cvr_weight", "volume_weight",
    "max_scale_pct", "scale_cooldown_hours", "max_daily_budget_increase",
    "broad_roas_threshold_multiplier", "broad_min_days_before_pause",
    "lla_scale_pct_bump", "lla_fatigue_spend_multiplier",
    "interest_days_decline_before_pause", "custom_max_scale_pct",
]


class EffectiveSettings:
    """Settings object that behaves like config.Settings but with DB overrides applied."""

    def __init__(self, base_settings, overrides: dict):
        self._base = base_settings
        self._overrides = overrides

    def __getattr__(self, name: str):
        if name.startswith("_"):
            return super().__getattribute__(name)
        if name in self._overrides and self._overrides[name] is not None:
            return self._overrides[name]
        return getattr(self._base, name)


def get_effective_settings(db: Session) -> EffectiveSettings:
    """Load env defaults merged with DB overrides. Use this in services instead of get_settings()."""
    from app.models import SettingsOverride

    base = get_settings()
    try:
        row = db.query(SettingsOverride).filter(SettingsOverride.id == "global").first()
        if row and row.overrides_json:
            overrides = json.loads(row.overrides_json)
        else:
            overrides = {}
    except Exception:
        overrides = {}

    return EffectiveSettings(base, overrides)
