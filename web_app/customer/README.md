# 📚 PUC Digital Bookstore Management System — Web Customer Application

Official Web Application platform for **Paññāsāstra University of Cambodia (PUC)** campus bookstore digitization, featuring both the **Student Customer Storefront** and the **Staff Manager Control Center**.

🌐 **Live Production Deployment**: [https://charming-rugelach-827e8e.netlify.app/](https://charming-rugelach-827e8e.netlify.app/)

---

## 📌 System Overview

The **PUC Digital Bookstore Web Application** is a full-stack e-commerce and bookstore management system designed for Paññāsāstra University of Cambodia (PUC).

* **Student Customer Storefront**: Students can browse and search course materials by department or keyword, inspect live stock levels, manage shopping carts, register/login securely with PBKDF2 SHA-256 encryption, checkout using Stripe, ABA Bank KHQR, or Direct Card, and receive a **Digital Receipt with a unique 6-Digit Pickup PIN & scannable HTML5 Canvas QR Code** for physical collection at PUC Campus Building A.
* **Staff Manager Control Center**: Authorized staff and managers can access the integrated **Manager Dashboard** (`#manager-dashboard`) to verify 6-digit pickup PINs, scan student QR tokens, inspect real-time sales analytics (Total Revenue, Business Worth, Total Orders), manage order fulfillment states (`Pending`, `Ready for Pickup`, `Picked Up`), register counter staff accounts, and manage textbook inventory.

---

## 📁 Repository Directory Structure (`web_app/customer/`)

```text
web_app/customer/
├── index.html                   # Single Page Application (Student Storefront & Staff Manager Dashboard)
├── server.py                    # Python REST API server (Flask/HTTP) with security & PIN generation
├── db_adapter.py                # Dual PostgreSQL (Render Cloud) & SQLite3 Database Adapter
├── init_db.py                   # Relational Database Schema Creator
├── reset_clean_db.py            # Clean Database Reset Utility
├── migrate_to_postgres.py       # PostgreSQL Cloud Migration Script
├── puc_bookstore.db             # Local Relational SQLite Database file
├── package.json                 # Project npm scripts & metadata
├── README.md                    # Detailed Web Application documentation
│
├── css/
│   └── styles.css               # PUC Modern Design System & CSS Stylesheet
│
├── js/
│   ├── app.js                   # Application Router, REST API Client, Cart, Checkout, QR/PIN Engine, & Manager Dashboard
│   └── data/
│       └── booksData.js         # Initial catalog seed data module
│
└── assets/
    └── images/
        └── puclogo.png          # Official PUC University Logo
```

---

## 🚀 Quick Start & Local Development

### 1. Launch Dev Server
```bash
# Navigate to the web app customer directory
cd web_app/customer

# Launch development server
python server.py 8000
```

Access the local web application at:  
👉 **`http://localhost:8000`**

### 2. Live Cloud URL
👉 **[https://charming-rugelach-827e8e.netlify.app/](https://charming-rugelach-827e8e.netlify.app/)**

---

## 🎨 Storefront UI Workflows & Screen Documentation

The application consists of **13 primary UI screens and interactive modules**:

| Screen # | Image Reference | UI Module / View | Feature & Capability Breakdown |
| :--- | :--- | :--- | :--- |
| **1** | `1. web-home-browse.png` | **Home Storefront Catalog (`#home`)** | Department filtering chips (Computer Science, Business, IT, etc.), hero section, dynamic book cards grid with stock indicators and pricing. |
| **2** | `2. web-search-filter.png` | **Global Search & Filter Bar** | Instant header search input (Title, Author, ISBN, Course Code) with real-time match count results header. |
| **3** | `3. web-book-details.png` | **Book Details View (`#book-details`)** | High-res cover artwork, category badge, real-time stock pill (`• X in stock`), student pricing, quantity stepper (`- 1 +`), full description, and "Add to Cart" CTA. |
| **4** | `4. web-cart.png` | **Session Shopping Cart (`#cart`)** | Dynamic cart list, item quantity controls, single-click item removal, live subtotal, processing fee breakdown ($0.50), total amount, and checkout CTA. |
| **5** | `5. web-login.png` | **Student Login Portal (`#login`)** | University student login interface, password visibility toggle, forgot password flow trigger, and link to account registration. |
| **6** | `6. web-create-account.png` | **Create Student Account (`#register`)** | Registration form requiring Full Name, Student ID (PUC format), Email, and Password with PBKDF2 SHA-256 security. |
| **7** | `7. web-checkout.png` | **Multi-Step Checkout (`#checkout`)** | 4-step order checkout: (1) Verified Student Info, (2) Store Pickup selection (Campus Building A), (3) Order Items breakdown, (4) Payment Selection (Stripe, ABA KHQR, Direct Card). |
| **8** | `8. web-payment-processing.png` | **Payment Processing Overlay** | Animated security shield modal displaying real-time payment validation and automated 6-Digit PIN generation. |
| **9** | `9. web-receipt-pickup-pin.png` | **Digital Receipt & Token (`#order-success`)** | Order confirmation page with `Paid` status, order number (`PUC-ORD-1025`), unique **6-Digit Pickup PIN** (`482913`), and scannable HTML5 Canvas QR Code. |
| **10** | `10. web-pickup-instructions.png` | **Store Pickup Instructions** | Detailed pickup guidance: Main Campus Building A, 1st Floor Counter, Mon-Fri 8:00 AM - 5:00 PM, Sat 8:00 AM - 12:00 PM. |
| **11** | `11. web-show-pickup-pin.png` | **Campus Pickup Token Screen** | Full-screen modal presenting student 6-Digit PIN and scannable QR code for physical bookstore counter validation. |
| **12** | `12. web-my-orders.png` | **Student Order History (`#my-orders`)** | Complete order history with fulfillment status badges (`Paid`, `Ready for Pickup`, `Picked Up`), order details, and pickup PIN recovery. |
| **13** | `13. web-account.png` | **Student Account Profile (`#account`)** | Student profile card, Student ID display, Edit Profile modal, Help & Support contacts (`support@puc.edu.kh`), and system info. |

---

## 🧑‍💼 Staff Manager Control Center (`#manager-dashboard`)

Authorized staff and managers can access the administrative dashboard directly in the Web Application:

1. **Real-Time Sales Metrics**:
   - **Total Revenue**: Cumulative revenue calculated across all completed orders.
   - **Business Worth**: Estimated inventory valuation across active catalog titles.
   - **Total Orders**: Live count of all customer purchase transactions.

2. **6-Digit PIN Verification Tool**:
   - Dedicated counter verification modal allowing staff to type a student's 6-digit PIN to lookup orders and process fulfillment.

3. **QR Code Scanner Modal**:
   - Camera/HTML5 QR code scanner modal to scan student digital receipt QR codes instantly at the counter.

4. **Order Fulfillment Pipeline**:
   - Order pipeline board categorized by status: `All`, `Pending`, `Ready for Pickup`, `Picked Up`.
   - One-click status transitions to inform students when books are ready for counter collection.

5. **Inventory & Stock Control**:
   - Live inventory table with stock adjustment controls to update textbook quantities.

6. **Staff Account Registration**:
   - Register new campus counter staff using the secure `PUC-STAFF-2026` verification authorization code.

---

## 🔒 Security Architecture

* **PBKDF2 SHA-256 Hashing**: Password security enforced with **PBKDF2 SHA-256** using 100,000 iterations and a unique salt per account.
* **Role-Based Access Control (RBAC)**:
  * **Customer Accounts (`role: 'customer'`)**: Restricted to browsing catalog, shopping cart, checkout, receipt token generation, and personal order history.
  * **Staff Accounts (`role: 'staff'`)**: Granted access to Manager Dashboard (`#manager-dashboard`), PIN verification, QR scanning, order status updates, and inventory management.
* **Session Token Authentication**: Requests require valid token headers for protected staff and user operations.

---

## 🗄️ Database Architecture

The application includes a dual database layer powered by `db_adapter.py`:

* **Cloud PostgreSQL (Production)**:
  Connects to Render Hosted PostgreSQL (`digital-bookstore-wm64.onrender.com`). Set environment variable:
  ```bash
  $env:DATABASE_URL="postgresql://user:password@render-host.onrender.com/puc_bookstore"
  python server.py 8000
  ```
* **Local SQLite3 (Offline Fallback)**:
  Automatically uses `puc_bookstore.db` when offline or when `DATABASE_URL` is omitted.

---

## 🔌 Key REST API Endpoints (`server.py`)

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/books` | Fetch all course textbooks with stock status | Public |
| `GET` | `/api/books/<id>` | Fetch detailed book information | Public |
| `POST` | `/api/login` | User/Staff authentication | Public |
| `POST` | `/api/register` | Student account registration | Public |
| `POST` | `/api/forgot-password` | Request password reset verification code | Public |
| `POST` | `/api/reset-password` | Submit new password with verification code | Public |
| `POST` | `/api/orders` | Create new order & generate 6-Digit Pickup PIN | Authenticated |
| `GET` | `/api/orders` | Fetch orders for current student or all (staff) | Authenticated |
| `GET` | `/api/orders/<id>` | Fetch specific order receipt & PIN token | Authenticated |
| `POST` | `/api/orders/verify-pin` | Verify student 6-digit pickup PIN | Staff Only |
| `PUT` | `/api/orders/<id>/status` | Update order fulfillment status | Staff Only |
| `POST` | `/api/staff/register` | Register new counter staff account | Staff Code Required |

---

## 🛠️ Technology Stack

* **Frontend**: HTML5, Vanilla CSS3 (Custom PUC Design System), Modern JavaScript (ES6 Modules, Dynamic View Router), QRious (HTML5 Canvas QR Code Engine).
* **Backend Server**: Python REST API (`server.py`) & Dual Database Adapter (`db_adapter.py`).
* **Database**: PostgreSQL (Render Cloud) / SQLite3 (`puc_bookstore.db` local).
* **Security**: PBKDF2 SHA-256 Password Encryption (100,000 rounds), Session Token Authentication.
* **Typography**: Google Fonts (`Inter`, `Outfit`, `JetBrains Mono`).
* **Icons**: FontAwesome 6.4.0.

---

© 2026 Paññāsāstra University of Cambodia (PUC) - Digital Bookstore Project