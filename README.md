# 📚 PUC Digital Bookstore - Full-Stack Ecosystem

A production-ready course book procurement system designed specifically for **Paññāsāstra University of Cambodia (PUC)**. This system synchronizes a **Flutter (Mobile/Web)** frontend with a **FastAPI (Python)** backend and a **PostgreSQL** relational database.

---

## 🚀 Key Features

### 🎓 For Students (Customers)
*   **Guest Browsing**: Search and filter course books by Department without an account.
*   **Smart Cart**: Real-time stock verification prevents over-ordering.
*   **Secure Checkout**: Professional **Stripe Credit Card** payment flow.
*   **Digital Token**: Instant generation of a unique 6-digit **Pickup PIN** and **QR Code**.
*   **Order History**: Full visibility of current pickup locations and past receipts.

### 🧑‍💼 For Staff & Admin
*   **Manager Dashboard**: Real-time business intelligence with **Revenue Trends** and **Total Assets Worth**.
*   **Fulfillment Flow**: Professional 3-step workflow (Prepare -> Verify -> Release).
*   **Inventory Control**: ISBN Metadata Import tool (Google Books API).
*   **Accountability**: Every fulfillment action is logged with the specific **Staff ID**.
*   **Staff Management**: Admin-only tool to create employee accounts.

---

## 🛠️ Technical Stack

*   **Frontend**: Flutter (supports Android, iOS, Web)
*   **Backend**: FastAPI (Python 3.11+)
*   **Database**: PostgreSQL
*   **Hosting**: Render (Database & API)
*   **Payment**: Stripe API

---

## ⚙️ Deployment Guide (Render.com)

### 1. Database Setup
1.  Create a **New PostgreSQL** instance on Render.
2.  Run `etl/schema.sql` using the Render Query tool or pgAdmin.

### 2. Backend API Setup
1.  Create a **New Web Service** on Render connected to your GitHub.
2.  Set **Build Command**: `pip install -r backend/requirements.txt`
3.  Set **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4.  Add your Database credentials to the **Environment Variables** section.

### 3. Flutter Sync
1.  Update `baseUrl` in `lib/services/api_service.dart` to your Render service URL.
2.  Build for web: `flutter build web`
3.  Build for mobile: `flutter build apk --release`

---

## 🔐 Credentials for Demo

| Account Type | Email | Password |
| :--- | :--- | :--- |
| **Root Admin** | `admin@puc.edu.kh` | `pass123` |
| **Staff Member** | Create via Dashboard | Assign via Admin |

---
© 2024 PUC Digital Bookstore - Academic Project
