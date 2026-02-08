"""Account CRUD and list."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account
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
