from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class VoucherCreate(BaseModel):
    code: str
    type: str
    uses_left: int
    expires: bool
    expiry_time: Optional[datetime]


class VoucherRedemption(BaseModel):
    code: str


class VoucherGet(BaseModel):
    code: str
