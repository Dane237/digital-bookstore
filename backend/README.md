# ⚡ PUC Bookstore Backend API

A central FastAPI backend service connecting the Flutter Mobile Application, Web applications, and Staff tools to the shared **PostgreSQL** database.

---

## 🚀 Features

### Core API Endpoints
- `POST /api/orders/`: Creates a customer order, generates a unique 6-digit pickup PIN, and saves it to PostgreSQL.
- `GET /api/books/`: Fetches available textbook catalog.
- `POST /api/login/`: Handles student & staff authentication with PBKDF2 password hashing verification.
- `GET /api/staff/analytics/`: Provides real-time revenue statistics, top-selling books, and total business value (cash + inventory).
- `GET /api/admin/isbn-lookup/{isbn}`: Integrated with Google Books API to auto-fill book details during inventory entry.

### Staff & Management
- **Staff Pickup Terminal**: Includes `staff_tool.py`, a dedicated CLI for staff to verify 6-digit PINs and mark orders as "Picked Up."
- **Order Workflow**: Endpoints to move orders from `Pending` → `Ready for Pickup` → `Picked Up`.
- **Inventory Management**: Add/Delete books and manage stock levels via admin-protected endpoints.

---

## ⚙️ Setup & Configuration

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**:
   - Create or update `backend/.env` with your PostgreSQL database credentials and SMTP settings for password resets:
     ```env
     DB_HOST=localhost
     DB_PORT=5432
     DB_NAME=puc_bookstore
     DB_USER=postgres
     DB_PASSWORD=yourpassword
     
     # Email Reset Settings (Optional)
     SENDER_EMAIL=your-email@gmail.com
     SENDER_APP_PASSWORD=your-app-password
     ```

3. **Run Dev Server**:
   ```bash
   python main.py
   ```
   The FastAPI server will start at **`http://localhost:8000`** with interactive docs at **`http://localhost:8000/docs`**.

4. **Run Staff Terminal**:
   ```bash
   python staff_tool.py
   ```

---

## 📱 Integration
- **Flutter Mobile App**: Points to `http://10.0.2.2:8000` (Android Emulator) or live endpoint. Supports Student, Staff, and Admin workflows.
- **Web App**: Connects to the backend for real-time inventory and order processing.

---
© 2026 PUC Digital Bookstore - Academic Project
