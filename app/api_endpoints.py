from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.models import VoucherCreate, VoucherGet, VoucherRedemption
from app.ocr_definitions import VOUCHER_TYPES, Voucher, BaseClass
from sqlalchemy.exc import IntegrityError

DATABASE_URL = "sqlite:///./_database.db"

appAPI = FastAPI()

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BaseClass.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Admin: Create a voucher
@appAPI.post("/voucher/")
def create_voucher(voucher: VoucherCreate, db: Session = Depends(get_db)):
    db_voucher = Voucher(
        code=voucher.code,
        type=voucher.type,  # using the enum type (SINGLE, MULTIPLE, X_TIMES)
        max_redemptions=voucher.max_redemptions,
        expires=voucher.expires,
        expiry_time=voucher.expiry_time
    )

    if voucher.type not in VOUCHER_TYPES:
        raise HTTPException(
            status_code=400, detail=f"Invalid voucher type. Allowed values are: {', '.join(VOUCHER_TYPES.keys())}")

    if voucher.expires and voucher.expiry_time is None:
        raise HTTPException(
            status_code=400, detail="Voucher expiry time is not set")

    if not voucher.expires and voucher.expiry_time is not None:
        voucher.expiry_time = None

    db.add(db_voucher)
    try:
        db.commit()
        db.refresh(db_voucher)
        return {"message": "Created voucher"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Voucher code already exists")


# Admin: Get every voucher
@appAPI.get("/vouchers/")
def get_vouchers(db: Session = Depends(get_db)):
    db_voucher = db.query(Voucher).all()
    if not db_voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")

    return {"vouchers": db_voucher}


# Admin: Get a specific voucher by code
@appAPI.get("/voucher/")
def get_voucher_by_code(voucher: VoucherGet, db: Session = Depends(get_db)):
    db_voucher = db.query(Voucher).filter(Voucher.code == voucher.code).first()

    if db_voucher is None:
        raise HTTPException(status_code=404, detail="Voucher not found")

    return {"voucher": db_voucher}


# Admin: Delete a specific voucher by code using VoucherGet
@appAPI.delete("/voucher/")
def delete_voucher(voucher: VoucherGet, db: Session = Depends(get_db)):
    # Query the database for the voucher by its code
    db_voucher = db.query(Voucher).filter(Voucher.code == voucher.code).first()

    # If no voucher is found, raise a 404 error
    if db_voucher is None:
        raise HTTPException(status_code=404, detail="Voucher not found")

    # Delete the voucher
    db.delete(db_voucher)
    db.commit()

    return {"message": f"Voucher with code '{voucher.code}' has been successfully deleted"}


# Client: Redeem a voucher
@appAPI.post("/redeem/")
def redeem_voucher(voucher: VoucherRedemption, db: Session = Depends(get_db)):
    db_voucher = db.query(Voucher).filter(Voucher.code == voucher.code).first()
    if db_voucher is None:
        raise HTTPException(status_code=404, detail="Voucher not found")

    if db_voucher.expires:
        if db_voucher.expiry_time < datetime.now():
            raise HTTPException(status_code=400, detail="Voucher has expired")

    if db_voucher.type != "multiple":
        if db_voucher.redeemed_count >= db_voucher.max_redemptions:
            raise HTTPException(
                status_code=400, detail="Voucher has been redeemed the maximum number of times")

    db_voucher.redeemed_count += 1
    db.commit()
    return {"message": "Voucher redeemed successfully"}
