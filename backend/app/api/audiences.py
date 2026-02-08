"""Audience listing and detail."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Audience
from app.schemas import AudienceResponse, AudienceDetail
from app.utils.cache import (
    cache_get, cache_set, PREFIX_AUDIENCES, TTL_AUDIENCES, _make_key,
)

router = APIRouter(prefix="/audiences", tags=["audiences"])


@router.get("", response_model=list[AudienceResponse])
def list_audiences(
    account_id: str = Query(..., description="Account ID"),
    db: Session = Depends(get_db),
):
    """List audiences (ad sets) for an account."""
    cache_key = PREFIX_AUDIENCES + _make_key("list", account_id)
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    audiences = db.query(Audience).filter(Audience.account_id == account_id).order_by(Audience.name).all()
    result = [AudienceResponse.model_validate(a) for a in audiences]
    cache_set(cache_key, result, TTL_AUDIENCES)
    return result


@router.get("/{audience_id}", response_model=AudienceDetail)
def get_audience(audience_id: str, db: Session = Depends(get_db)):
    """Get one audience by id."""
    cache_key = PREFIX_AUDIENCES + _make_key("detail", audience_id)
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    audience = db.query(Audience).filter(Audience.id == audience_id).first()
    if not audience:
        raise HTTPException(status_code=404, detail="Audience not found")
    result = AudienceDetail.model_validate(audience)
    cache_set(cache_key, result, TTL_AUDIENCES)
    return result
