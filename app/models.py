from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from app.voucher_models import VOUCHER_TYPES


class VoucherCreate(BaseModel):
    code: str
    type: str
    uses_left: int
    expires: bool
    expiry_time: Optional[datetime]

    # Validator for `uses_left` to ensure it's correctly set based on `type`
    @field_validator("uses_left")
    def check_uses_left_for_type(cls, v, info):
        # Use info.data to access other field values
        voucher_type = info.data.get("type")
        if voucher_type == "single" and v != 1:
            raise ValueError(
                "For a 'single' voucher, uses_left must be exactly 1.")
        if voucher_type == "xtimes" and v < 2:
            raise ValueError(
                "uses_left must be greater than 1 for 'xtimes' vouchers.")
        return v

    # Validator for `type` to ensure it's a valid voucher type
    @field_validator("type")
    def check_voucher_type(cls, v):
        if v not in VOUCHER_TYPES:
            raise ValueError(
                f"Invalid voucher type. Allowed values are: {', '.join(VOUCHER_TYPES.keys())}")
        return v

    # Validator for `expiry_time` when `expires` is True, `expiry_time` must be provided
    @field_validator("expiry_time")
    def check_expiry_time_required(cls, v, info):
        expires = info.data.get("expires")
        if expires and not v:
            raise ValueError(
                "expiry_time must be provided if 'expires' is True.")
        return v


class VoucherRedemption(BaseModel):
    code: str
