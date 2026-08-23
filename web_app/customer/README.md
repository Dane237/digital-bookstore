# PUC Digital Bookstore Management System — Full-Stack Web Application

Official Web Application for **Paññāsāstra University of Cambodia (PUC)** physical campus bookstore digitization.

---

## 📌 Project Overview
The **PUC Digital Bookstore System** is a full-stack student e-commerce platform for Paññāsāstra University of Cambodia (PUC).

* **Customer Experience**: Students can search for required course materials by department or course code (e.g., `CS301`, `CS202`), view textbook details, add items to cart, register a student account (enforcing PBKDF2 SHA-256 password security), complete payment via ABA Mobile Banking / Stripe, and receive a **Digital Receipt with a unique 6-Digit Pickup PIN / QR Code** for physical collection at the PUC campus counter.

---

## 📁 Repository Directory Structure

```text
PUC Digital Bookstore/
├── index.html                   # Primary HTML5 application viewport (Student Storefront Views)
├── server.py                    # Full-Stack Python REST API server with security hashing
├── db_adapter.py                # Dual SQLite3 & PostgreSQL Database Adapter
├── init_db.py                   # Production Database Schema Creator
├── reset_clean_db.py            # 1-Click Clean Empty Database Reset Tool
├── migrate_to_postgres.py       # 1-Click PostgreSQL Migration Utility
├── puc_bookstore.db             # Relational Database file
├── README.md                    # Project documentation & testing guide
│
├── css/
│   └── styles.css               # PUC Design System & UI stylesheet
│
├── js/
│   ├── app.js                   # Application router, REST API handlers & PIN canvas engine
│   └── data/
│       └── booksData.js         # Catalog initial state module
│
└── assets/
    └── images/
        └── puclogo.png          # Official PUC University Emblem Logo
```

---

## ⚡ Quick Start & Development Server

### Run Dev Server
```bash
python server.py 8000
```

Access the application live in your browser at:  
👉 **`http://localhost:8000`**

---

## 🧪 Student Customer Storefront Guidelines
1. **Catalog Browsing**: Students navigate to `http://localhost:8000` to view live textbooks.
2. **Academic Filters**: Filter catalog by Department dropdown or Course Code search (e.g. `CS301`, `CS202`).
3. **Mandatory Account Registration**: Adding a textbook to cart and clicking **"Proceed to Checkout"** enforces mandatory authentication. Access is strictly blocked until students sign in or create an account.
4. **PBKDF2 SHA-256 Security**: When students register, their password is encrypted using PBKDF2 SHA-256 with 100,000 hashing rounds + salt before saving to `users` table.
5. **Digital Receipt & 6-Digit Pickup PIN**: After selecting ABA Mobile Banking or Credit Card payment, students receive a digital receipt containing a unique **6-Digit Pickup PIN** (e.g., `482913`) and an HTML5 Canvas QR Code.

---

## 🚀 Key Functional Features

1. **Academic Course Search & Filter:** Filter textbooks by Department (Computer Science, Business, IT), Course Code (`CS101`, `CS201`, `CS202`, `CS301`, `CS302`, `CS303`), and In Stock status.
2. **Interactive Book Details:** High-res textbook artwork, stock status pill, student price calculation, and quantity steppers (`- 1 +`).
3. **Session Cart & Order Breakdown:** Live subtotal calculation, administrative processing fee breakdown (`$0.50`), line item modification, and trash deletion.
4. **Mandatory Authentication Flow:** User registration & login interface enforcing PBKDF2 SHA-256 password hashing. Every student must register to purchase books.
5. **Secure Checkout & Stripe Gateway:** Multi-step checkout selecting pickup method, payment option (Mobile Banking vs Credit Card), and payment authorization simulation.
6. **Digital Receipt & 6-Digit Pickup PIN Engine:** Generates a unique 6-digit PIN (e.g. `482913`) and renders a **scannable QR Code canvas** for campus bookstore verification.aphs** (Chart.js Bar & Doughnut charts). Student accounts (`role: 'customer'`) are strictly blocked from accessing staff views and API endpoints.

---

## 🔒 Security & Role-Based Access Control (RBAC)

The application enforces strict multi-level role authorization:

* **Customer / Student Accounts (`role: 'customer'`)**: Restricted to browsing course textbooks, adding to cart, checkout, payment processing, generating digital pickup PINs, and viewing personal order history (`#my-orders` / `#account`). Attempts to access `#staff-dashboard` are blocked with an access control error toast (`🔐 Access Denied: Staff/Admin credentials required`).
* **Staff & Admin Accounts (`role: 'staff'`)**: Authorized to log into the Administrative Control Center (`admin@puc.edu.kh`), ingest new course materials, import ISBN metadata, verify customer 6-digit PINs, and inspect sales analytics.
* **Backend API Protection**: Server endpoints (`/api/admin/*` and `/api/staff/*`) require valid session tokens associated with a staff/admin user account and return `HTTP 403 Forbidden` if invoked by unauthenticated or customer accounts.

---

## 🗄️ Database Options (Render Hosted PostgreSQL)

The system connects directly to the production **Render Hosted PostgreSQL Database** shared with the Flutter Mobile App:

* **Production Render PostgreSQL**: Pass `DATABASE_URL` environment variable or rely on backend environment settings (`digital-bookstore-wm64.onrender.com`).
  ```bash
  $env:DATABASE_URL="postgresql://user:password@render-host.onrender.com/puc_bookstore"
  python server.py 8000
  ```

---

## 🛠️ Technology Stack
* **Frontend:** HTML5, Vanilla CSS3 (Custom PUC Design System), JavaScript (ES6 Modules & Dynamic DOM Router), QRious (HTML5 Canvas QR Generator).
* **Backend:** Python Flask REST API (`server.py`) & Database Adapter (`db_adapter.py`).
* **Database:** Render Hosted PostgreSQL (`https://digital-bookstore-wm64.onrender.com/api`).
* **Security:** PBKDF2 SHA-256 password hashing (100,000 rounds + salt), session token authentication.
* **Typography:** Google Fonts (`Inter`, `Outfit`, `JetBrains Mono`).
* **Icons:** FontAwesome 6.4.0.