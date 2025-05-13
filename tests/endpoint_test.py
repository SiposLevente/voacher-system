import os
os.environ["DATABASE_URL"] = "sqlite:///./test_database.db"  # noqa

import pytest
from app.ocr_definitions import VOUCHER_TYPES, Voucher
from fastapi.testclient import TestClient
from app.api_endpoints import appAPI, SessionLocal, engine


# Initialize the test client
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

        if os.path.exists("./test_database.db"):
            os.remove("./test_database.db")
    except Exception as e:
        print(f"Error deleting the database: {e}")


def test_create_voucher(db_session):
    for type in VOUCHER_TYPES.keys():
        payload = {
            "code": f"{type.upper()}123",
            "type": type,
            "uses_left": 5,
            "expires": "true",
            "expiry_time": "2025-12-31T23:59:59"
        }
        response = client.post("/voucher/", json=payload)
        assert response.status_code == 200
        assert response.json()["message"] == "Created voucher"


def test_create_voucher_missing_code(db_session):
    payload = {
        "code": "INVALID123",
        "type": "xtimes",
        "uses_left": 5,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 422


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
    # Create the first voucher
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Created voucher"
    # Attempt to create a duplicate voucher
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
    # Create the voucher
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    # Retrieve the voucher
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
    # Delete the voucher
    response = client.delete(f"/voucher/?code={payload['code']}")
    assert response.status_code == 200
    assert response.json()[
        "message"] == f"Voucher with code '{payload['code']}' has been successfully deleted"
    # Verify the voucher no longer exists
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
    # Create the voucher
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200
    # Redeem the voucher
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

    # Create the voucher
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200

    for _ in range(number_of_redeems):
        # Redeem the voucher once
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

    # Create the voucher
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200

    for _ in range(number_of_redeems):
        # Redeem the voucher once
        redeem_payload = {"code": payload["code"]}
        response = client.post("/redeem/", json=redeem_payload)

    response = client.post("/redeem/", json=redeem_payload)
    assert response.status_code == 200
