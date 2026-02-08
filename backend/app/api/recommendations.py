"""Trigger and fetch recommendations."""
from sqlalchemy import func as sa_func
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Audience, MetricSnapshot, Recommendation
from app.schemas import RecommendationResponse
from app.utils.cache import (
    cache_get, cache_set, cache_invalidate_prefix,
    PREFIX_RECOMMENDATIONS, TTL_RECOMMENDATIONS,
    PREFIX_BENCHMARKS, PREFIX_METRICS, _make_key,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationResponse])
def list_recommendations(
    account_id: str = Query(..., description="Account ID"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List latest recommendations for an account's audiences."""
    cache_key = PREFIX_RECOMMENDATIONS + _make_key("list", account_id, limit)
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    recs = (
        db.query(Recommendation)
        .join(Audience)
        .filter(Audience.account_id == account_id)
        .order_by(Recommendation.generated_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for r in recs:
        data = RecommendationResponse.model_validate(r)
        data.audience_name = r.audience.name
        data.audience_type = r.audience.audience_type
        out.append(data)
    cache_set(cache_key, out, TTL_RECOMMENDATIONS)
    return out


@router.post("/generate")
async def generate_recommendations(
    account_id: str = Query(..., description="Account ID"),
    db: Session = Depends(get_db),
):
    """Trigger recommendation generation (rules -> Claude), then return new recommendations."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check if there's enough data to generate
    audiences_with_data = (
        db.query(sa_func.count(sa_func.distinct(MetricSnapshot.audience_id)))
        .join(Audience)
        .filter(Audience.account_id == account_id, MetricSnapshot.window_days == 7)
        .scalar() or 0
    )
    if audiences_with_data == 0:
        raise HTTPException(
            status_code=400,
            detail="No synced data available. Run a sync first to pull audience metrics from Meta.",
        )

    from app.services.claude_analyzer import generate_recommendations_for_account
    try:
        results = generate_recommendations_for_account(db, account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Invalidate stale caches after new recommendations are generated
    cache_invalidate_prefix(PREFIX_RECOMMENDATIONS)
    cache_invalidate_prefix(PREFIX_BENCHMARKS)
    cache_invalidate_prefix(PREFIX_METRICS)

    return {"recommendations": results, "count": len(results)}
