"""Threshold and config endpoints with DB persistence."""
import json
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import SettingsOverride
from app.schemas import SettingsResponse, SettingsUpdate
from app.utils.cache import cache_get, cache_set, cache_invalidate_prefix, PREFIX_SETTINGS, TTL_SETTINGS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

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


def _get_overrides(db: Session) -> dict:
    """Load overrides from DB (single-row table)."""
    row = db.query(SettingsOverride).filter(SettingsOverride.id == "global").first()
    if not row:
        return {}
    try:
        return json.loads(row.overrides_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def _build_settings_response(db: Session) -> SettingsResponse:
    """Merge env defaults with DB overrides."""
    s = get_settings()
    overrides = _get_overrides(db)

    values = {}
    for field in _SETTINGS_FIELDS:
        # DB override takes priority over env default
        if field in overrides and overrides[field] is not None:
            values[field] = overrides[field]
        else:
            values[field] = getattr(s, field)

    return SettingsResponse(**values)


@router.get("", response_model=SettingsResponse)
def get_settings_endpoint(db: Session = Depends(get_db)):
    """Return current config (env defaults merged with DB overrides)."""
    cache_key = PREFIX_SETTINGS + "current"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    result = _build_settings_response(db)
    cache_set(cache_key, result, TTL_SETTINGS)
    return result


@router.patch("", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    """Update settings overrides. Only provided (non-null) fields are changed."""
    # Load existing overrides
    row = db.query(SettingsOverride).filter(SettingsOverride.id == "global").first()
    if not row:
        row = SettingsOverride(id="global", overrides_json="{}")
        db.add(row)

    try:
        current = json.loads(row.overrides_json)
    except (json.JSONDecodeError, TypeError):
        current = {}

    # Merge in new values (only non-null fields from the payload)
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        # Nothing to update
        return _build_settings_response(db)

    current.update(update_data)
    row.overrides_json = json.dumps(current)
    db.commit()

    logger.info(f"Settings updated: {list(update_data.keys())}")

    # Invalidate cache
    cache_invalidate_prefix(PREFIX_SETTINGS)

    return _build_settings_response(db)


@router.post("/reset", response_model=SettingsResponse)
def reset_settings(db: Session = Depends(get_db)):
    """Reset all settings to env defaults (clear DB overrides)."""
    row = db.query(SettingsOverride).filter(SettingsOverride.id == "global").first()
    if row:
        row.overrides_json = "{}"
        db.commit()

    cache_invalidate_prefix(PREFIX_SETTINGS)
    logger.info("Settings reset to defaults")

    return _build_settings_response(db)
