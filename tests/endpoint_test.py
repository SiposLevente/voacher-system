import pytest
from fastapi.testclient import TestClient
from app.api_endpoints import SessionLocal, appAPI
from app.ocr_definitions import Voucher

# Initialize the test client
client = TestClient(appAPI)


@pytest.fixture(scope="function")
def db_session():
    # Create a new session
    db = SessionLocal()

    # Clear existing data before each test
    db.query(Voucher).delete()  # Clear the Voucher table
    db.commit()

    # Yield the session to the test
    yield db

    # Cleanup after the test
    db.query(Voucher).delete()  # Clear the Voucher table after test
    db.commit()

    # Close the session
    db.close()


# Test creating a voucher
def test_create_voucher(db_session):
    payload = {
        "code": "XTIMES123",
        "type": "xtimes",
        "max_redemptions": 5,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200  # Assuming a 200 status code for success
    # You can update the below assertions based on the actual response you expect
    assert response.json()["message"] == "Created voucher"


# Test voucher creation with missing fields (e.g., missing 'code')
def test_create_voucher_missing_code(db_session):
    payload = {
        "type": "xtimes",
        "max_redemptions": 5,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    # Expecting validation error due to missing 'code'
    assert response.status_code == 422


# Test invalid voucher creation (invalid data type for 'max_redemptions')
def test_create_voucher_invalid_data(db_session):
    payload = {
        "code": "INVALID123",
        "type": "xtimes",
        "max_redemptions": "five",  # Invalid type, should be an integer
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"
    }
    response = client.post("/voucher/", json=payload)
    # Expecting validation error due to invalid 'max_redemptions'
    assert response.status_code == 422


# Test voucher creation with an expired date
def test_create_voucher_expired_date(db_session):
    payload = {
        "code": "EXPIRED1233",
        "type": "xtimes",
        "max_redemptions": 3,
        "expires": "true",
        "expiry_time": "2020-12-31T23:59:59"  # An expired date
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200


# Test voucher creation with a future expiry time
def test_create_voucher_future_expiry(db_session):
    payload = {
        "code": "FUTURE124563",
        "type": "xtimes",
        "max_redemptions": 2,
        "expires": "true",
        "expiry_time": "2025-12-31T23:59:59"  # A valid future expiry time
    }
    response = client.post("/voucher/", json=payload)
    assert response.status_code == 200  # Assuming success with valid data
    assert response.json()["message"] == "Created voucher"


# Test voucher creation with an invalid expiry time format
def test_create_voucher_invalid_expiry_time(db_session):
    payload = {
        "code": "INVALIDTIME1423",
        "type": "xtimes",
        "max_redemptions": 3,
        "expires": "true",
        "expiry_time": "31-12-2025"  # Invalid format
    }
    response = client.post("/voucher/", json=payload)
    # Expecting validation error due to invalid expiry time format
    assert response.status_code == 422
