# Voucher Redemption Service

## Overview
This project implements a **Voucher Management and Redemption Service** using **FastAPI** and **SQLAlchemy**. It provides functionality for creating, managing, and redeeming vouchers with various features, including single, multiple, and X-times redemption. The service also supports voucher expiration.



## Features

* **Voucher Creation**: Create vouchers with different types and expiry times.
* **Voucher Redemption**: Redeem vouchers with different conditions (single, multiple, and X-times).
* **Expiry Handling**: Vouchers can be redeemed only before a specific expiration time.
* **Voucher Types**:
  * **Single**: Can be redeemed only once.
  * **Multiple**: Can be redeemed multiple times.
  * **X-times**: Can be redeemed a set number of times.

## Tech Stack

* **FastAPI**: For building the RESTful API.
* **SQLAlchemy**: For database management.
* **SQLite**: The default database used for the project.
* **pytest**: For running tests.

## Requirements
* Python 3.x
* Install the dependencies by running:
```bash
pip install -r requirements.txt
```

## Running the Service
To run the service locally, use the following command:

```bash
 uvicorn app.api_endpoints:appAPI --reload
```

This will start the FastAPI application on http://127.0.0.1:8000.

## API Endpoints


### Create a Voucher
- **URL**: `/voucher/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "code": "STRING",
    "type": "STRING",
    "uses_left": "INTEGER",
    "expires": "BOOLEAN",
    "expiry_time": "STRING" (optional, only required if expires is true)
  }
  ```
  - `code`: The unique code for the voucher.
  - `type`: The type of the voucher (can be "single", "multiple", or "xtimes").
  - `uses_left`: The number of times the voucher can be used.
  - `expires`: A boolean indicating whether the voucher has an expiry date.
  - `expiry_time`: A string representing the expiration date in ISO format (only required if `expires` is `true`).
  
- **Responses**:
  - **200 OK**:
    ```json
    {
      "message": "Created voucher"
    }
    ```
  - **400 Bad Request**:
    - If the voucher type is invalid.
    - If `uses_left` is less than 2 for an "xtimes" voucher.
    - If the voucher code already exists.

- **Example Request**:
  ```json
  {
    "code": "NEWVOUCHER123",
    "type": "xtimes",
    "uses_left": 3,
    "expires": true,
    "expiry_time": "2025-12-31T23:59:59"
  }
  ```



### Get All Vouchers
- **URL**: `/vouchers/`
- **Method**: `GET`
  
- **Response**:
  - **200 OK**: A list of all vouchers.
    ```json
    {
      "vouchers": [
        {
          "id": "INTEGER",
          "code": "STRING",
          "type": "STRING",
          "uses_left": "INTEGER",
          "expires": "BOOLEAN",
          "expiry_time": "STRING"
        }
      ]
    }
    ```
  - **404 Not Found**: If no vouchers are found.



### Get a Specific Voucher by Code
- **URL**: `/voucher/`
- **Method**: `GET`
- **Query Parameters**:
  - `code`: The unique voucher code to retrieve.

- **Response**:
  - **200 OK**: Details of the voucher.
    ```json
    {
      "voucher": {
        "id": "INTEGER",
        "code": "STRING",
        "type": "STRING",
        "uses_left": "INTEGER",
        "expires": "BOOLEAN",
        "expiry_time": "STRING"
      }
    }
    ```
  - **404 Not Found**: If the voucher with the specified code does not exist.



### Delete a Voucher by Code
- **URL**: `/voucher/`
- **Method**: `DELETE`
- **Query Parameters**:
  - `code`: The unique voucher code to delete.

- **Response**:
  - **200 OK**: 
    ```json
    {
      "message": "Voucher with code 'code' has been successfully deleted"
    }
    ```
  - **404 Not Found**: If the voucher with the specified code does not exist.



### Redeem a Voucher
- **URL**: `/redeem/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "code": "STRING"
  }
  ```
  - `code`: The unique voucher code to redeem.

- **Response**:
  - **200 OK**: 
    ```json
    {
      "message": "Voucher redeemed successfully"
    }
    ```
  - **400 Bad Request**: 
    - If the voucher has expired.
    - If the voucher has already been redeemed the maximum number of times.
    - If the voucher type is not "multiple" and has already been used.
  - **404 Not Found**: If the voucher with the specified code does not exist.



## Error Handling
In case of errors, the API returns an appropriate HTTP status code along with an error message. For example:

- **400 Bad Request**: Invalid input or missing required fields.
- **404 Not Found**: Resource (voucher) not found.
- **500 Internal Server Error**: Server-side error.

## Testing

You can run the tests using `pytest`:

```bash
pytest
```
The tests are located in the `tests` folder and cover voucher creation, redemption, and edge cases.