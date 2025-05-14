from datetime import datetime
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_database.db"  # noqa

import pytest
from app.voucher_models import Voucher
from fastapi.testclient import TestClient
from app.api_endpoints import appAPI, SessionLocal, engine

client = TestClient(appAPI)


@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    db.query(Voucher).delete()
    db.commit()
    yield db
    db.query(Voucher).delete()
    db.commit()
    db.close()


@pytest.fixture(scope="session", autouse=True)
def cleanup_db():
    yield
    try:
        engine.dispose()
        if os.path.exists("./_test_database.db"):
            os.remove("./_test_database.db")
    except Exception as e:
        print(f"Error deleting the database: {e}")


@pytest.mark.parametrize(
    "voucher_type, code, uses_left, expires, expiry_time",
    [
        ("single", "SINGLE123", 1, True, "2025-12-31T23:59:59"),
        ("multiple", "MULTIPLE123", 5, True, "2025-12-31T23:59:59"),
        ("xtimes", "XTIMES123", 5, True, "2025-12-31T23:59:59"),
    ]
)
def test_create_voucher(db_session, voucher_type, code, uses_left, expires, expiry_time):
    payload = {
        "code": code,
        "type": voucher_type,
        "uses_left": uses_left,
        "expires": expires,
        "expiry_time": expiry_time,
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Created voucher"


def test_create_voucher_missing_code(db_session):
    payload = {
        "type": "xtimes",
        "uses_left": 5,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 422


def test_create_voucher_invalid_data(db_session):
    payload = {
        "code": "INVALID123",
        "type": "xtimes",
        "uses_left": "five",
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 422


def test_create_voucher_duplicate_code(db_session):
    payload = {
        "code": "DUPLICATE123",
        "type": "xtimes",
        "uses_left": 5,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Created voucher"
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 400
    assert "code" in response.json()["detail"]


def test_get_existing_voucher(db_session):
    payload = {
        "code": "EXISTING123",
        "type": "xtimes",
        "uses_left": 5,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    get_payload = {
        "code": "EXISTING123",
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    response = client.get(f"/voucher/?code={get_payload['code']}")
    assert response.status_code == 200
    assert response.json()["voucher"]["code"] == get_payload["code"]


def test_delete_existing_voucher(db_session):
    payload = {
        "code": "DELETE123",
        "type": "xtimes",
        "uses_left": 5,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Created voucher"
    response = client.delete(f"/voucher/?code={payload['code']}")
    assert response.status_code == 200
    assert response.json()[
        "message"] == f"Voucher with code '{payload['code']}' has been successfully deleted"
    response = client.get(f"/voucher/?code={payload['code']}")
    assert response.status_code == 404


def test_redeem_voucher_success(db_session):
    payload = {
        "code": "REDEEM123",
        "type": "xtimes",
        "uses_left": 5,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    redeem_payload = {"code": payload["code"]}
    response = client.post("/redeem/", json=redeem_payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Voucher redeemed successfully"


def test_redeem_voucher_exceed_limit(db_session):
    number_of_redeems = 3
    payload = {
        "code": "LIMIT123",
        "type": "xtimes",
        "uses_left": number_of_redeems,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    for _ in range(number_of_redeems):
        redeem_payload = {"code": payload["code"]}
        response = client.post("/redeem/", json=redeem_payload)
    response = client.post("/redeem/", json=redeem_payload)
    assert response.status_code == 400
    assert "Voucher has been redeemed the maximum number of times" in response.json()[
        "detail"]


def test_redeem_multiple_times(db_session):
    number_of_redeems = 3
    payload = {
        "code": "MULTIPLE123",
        "type": "multiple",
        "uses_left": number_of_redeems,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    for _ in range(number_of_redeems):
        redeem_payload = {"code": payload["code"]}
        response = client.post("/redeem/", json=redeem_payload)
    response = client.post("/redeem/", json=redeem_payload)
    assert response.status_code == 200


def test_create_voucher_invalid_expiry_date(db_session):
    payload = {
        "code": "INVALID_EXPIRY123",
        "type": "xtimes",
        "uses_left": 5,
        "expires": True,
        "expiry_time": "invalid-date-format"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 422
    assert "Input should be a valid datetime or date, invalid character in year" in response.json()[
        "detail"][0]["msg"]


def test_redeem_expired_voucher(db_session):
    expired_payload = {
        "code": "EXPIRED123",
        "type": "xtimes",
        "uses_left": 5,
        "expires": True,
        "expiry_time": "2023-01-01T00:00:00"
    }
    response = client.post("/voucher/", json=expired_payload)
    assert response.status_code == 200
    redeem_payload = {"code": expired_payload["code"]}
    response = client.post("/redeem/", json=redeem_payload)
    assert response.status_code == 400
    assert "Voucher has expired" in response.json()["detail"]


def test_get_all_vouchers(db_session):
    # Create a few vouchers first
    payload1 = {
        "code": "SINGLE123",
        "type": "single",
        "uses_left": 1,
        "expires": True,
        "expiry_time": "2025-12-31T23:59:59"
    }
    payload2 = {
        "code": "MULTIPLE123",
        "type": "multiple",
        "uses_left": 5,
        "expires": True,
        "expiry_time": "2025-12-31T23:59:59"
    }
    client.post("/voucher/", json=payload1)
    client.post("/voucher/", json=payload2)

    # Now test retrieving all vouchers
    response = client.get("/vouchers/")
    assert response.status_code == 200
    assert "vouchers" in response.json()
    assert len(response.json()["vouchers"]) > 0


def test_create_voucher_invalid_type(db_session):
    payload = {
        "code": "INVALIDTYPE123",
        "type": "invalid",  # Invalid type
        "uses_left": 5,
        "expires": True,
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 422


def test_redeem_expired_exact_date(db_session):
    payload = {
        "code": "EXACTEXPIRY123",
        "type": "xtimes",
        "uses_left": 5,
        "expires": True,
        "expiry_time": datetime.now().isoformat()  # Set expiry to the current time
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    redeem_payload = {"code": payload["code"]}
    response = client.post("/redeem/", json=redeem_payload)
    assert response.status_code == 400
    assert "Voucher has expired" in response.json()["detail"]


def test_create_xtimes_voucher_invalid_uses_left(db_session):
    payload = {
        "code": "INVALIDXTIMES123",
        "type": "xtimes",
        "uses_left": 1,  # Invalid for xtimes
        "expires": True,
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 422


def test_redeem_non_existent_voucher(db_session):
    redeem_payload = {"code": "NONEXISTENT123"}
    response = client.post("/redeem/", json=redeem_payload)
    assert response.status_code == 404
    assert "Voucher not found" in response.json()["detail"]


def test_delete_non_existent_voucher(db_session):
    response = client.delete("/voucher/?code=NONEXISTENT123")
    assert response.status_code == 404
    assert "Voucher not found" in response.json()["detail"]
