from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AccountBase(BaseModel):
    meta_account_id: str
    account_name: Optional[str] = None


class AccountCreate(AccountBase):
    access_token: str
    token_expires_at: Optional[datetime] = None


class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AccountList(BaseModel):
    accounts: list[AccountResponse]
