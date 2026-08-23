# PUC Bookstore Backend API

A lightweight FastAPI backend that connects the Flutter mobile app to the MySQL database.

## Features
- `POST /api/orders/`: Creates an order, generates a pickup PIN, and saves it to MySQL.
- `GET /api/books/`: Returns a list of available books.

## Setup

1.  **Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    - Update `backend/.env` with your MySQL credentials.
    - Ensure `DB_NAME=puc_bookstore` matches the schema you set up.

3.  **Run**:
    ```bash
    python main.py
    ```
    The server will start at `http://localhost:8000`.

## Integration with Flutter
The Flutter app is configured to use `10.0.2.2:8000` which points to this backend when running in the Android Emulator.
