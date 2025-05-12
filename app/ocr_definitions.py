from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base


VOUCHER_TYPES = {
    "single": "single use voucher",
    "multiple": "multiple use voucher",
    "xtimes": "xtimes voucher"}

BaseClass = declarative_base()


class Voucher(BaseClass):
    __tablename__ = "vouchers"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    type = Column(String)
    max_redemptions = Column(Integer)
    redeemed_count = Column(Integer, default=0)
    expires = Column(Boolean, default=False)
    expiry_time = Column(DateTime, nullable=True)
