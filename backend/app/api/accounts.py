"""Account CRUD and list."""
from sqlalchemy import func as sa_func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Audience, MetricSnapshot
from app.schemas import AccountResponse, AccountList
from app.utils.cache import (
    cache_get, cache_set, PREFIX_ACCOUNTS, TTL_ACCOUNTS, _make_key,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=AccountList)
def list_accounts(db: Session = Depends(get_db)):
    """List all connected Meta ad accounts."""
    cache_key = PREFIX_ACCOUNTS + "all"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    accounts = db.query(Account).order_by(Account.created_at.desc()).all()
    result = AccountList(accounts=[AccountResponse.model_validate(a) for a in accounts])
    cache_set(cache_key, result, TTL_ACCOUNTS)
    return result


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: str, db: Session = Depends(get_db)):
    """Get one account by id."""
    cache_key = PREFIX_ACCOUNTS + _make_key(account_id)
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    result = AccountResponse.model_validate(account)
    cache_set(cache_key, result, TTL_ACCOUNTS)
    return result


@router.get("/{account_id}/sync-status")
def get_sync_status(account_id: str, db: Session = Depends(get_db)):
    """Return last sync time and data availability for an account."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    audience_count = db.query(sa_func.count(Audience.id)).filter(
        Audience.account_id == account_id
    ).scalar() or 0

    snapshot_count = (
        db.query(sa_func.count(MetricSnapshot.id))
        .join(Audience)
        .filter(Audience.account_id == account_id)
        .scalar() or 0
    )

    # Count audiences that have at least one 7d snapshot (needed for generate)
    audiences_with_data = (
        db.query(sa_func.count(sa_func.distinct(MetricSnapshot.audience_id)))
        .join(Audience)
        .filter(Audience.account_id == account_id, MetricSnapshot.window_days == 7)
        .scalar() or 0
    )

    return {
        "last_synced_at": account.last_synced_at.isoformat() if account.last_synced_at else None,
        "audience_count": audience_count,
        "snapshot_count": snapshot_count,
        "audiences_with_data": audiences_with_data,
        "can_generate": audiences_with_data > 0,
    }
