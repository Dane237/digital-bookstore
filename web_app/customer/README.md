# 📚 PUC Digital Bookstore System — Web Customer Application

Official Web Application platform for **Paññāsāstra University of Cambodia (PUC)** campus bookstore digitization, designed exclusively for **Student Customers**.

🌐 **Live Production Deployment**: [https://unrivaled-piroshki-69f896.netlify.app/](https://unrivaled-piroshki-69f896.netlify.app/)

---

## 📌 System Overview

The **PUC Digital Bookstore Web Application** is a full-stack e-commerce storefront designed for Paññāsāstra University of Cambodia (PUC) student customers.

* **Student Customer Storefront**: Students can browse and search course materials by department or keyword, inspect live stock levels, manage shopping carts, register/login securely with PBKDF2 SHA-256 encryption, checkout using Stripe, ABA Bank KHQR, or Direct Card, and receive a **Digital Receipt with a unique 6-Digit Pickup PIN & scannable HTML5 Canvas QR Code** for physical collection at PUC Campus Building A.

> [!NOTE]
> **Staff & Admin Management**: Counter staff and admins perform order fulfillment, 6-digit PIN verification, stock management, and sales monitoring using the **Flutter Mobile App** ([`mobile_app/`](../../mobile_app/README.md)) and **Staff Terminal CLI** ([`backend/`](../../backend/README.md)).

---

## 📁 Repository Directory Structure (`web_app/customer/`)

```text
web_app/customer/
├── index.html                   # Single Page Application (Student Storefront)
├── server.py                    # Python REST API server (Flask/HTTP) with security & PIN generation
├── db_adapter.py                # PostgreSQL Database Adapter
├── init_db.py                   # Relational Database Schema Creator
├── package.json                 # Project npm scripts & metadata
├── README.md                    # Detailed Web Application documentation
│
├── css/
│   └── styles.css               # PUC Modern Design System & CSS Stylesheet
│
├── js/
│   ├── app.js                   # Application Router, REST API Client, Cart, Checkout, QR/PIN Engine
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
👉 **[https://unrivaled-piroshki-69f896.netlify.app/](https://unrivaled-piroshki-69f896.netlify.app/)**


---

## 🎨 Storefront UI Workflows & Screen Documentation

The application consists of primary UI screens and interactive modules for student customers:

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

## 🔒 Security Architecture

* **PBKDF2 SHA-256 Hashing**: Password security enforced with **PBKDF2 SHA-256** using 100,000 iterations and a unique salt per account.
* **Customer Authentication**: Protected student ordering, digital receipt tokens, and order history access.
* **Session Token Authentication**: Requests require valid token headers for protected user operations.

---

## 🗄️ Database Architecture

The application connects directly to PostgreSQL via `db_adapter.py`:

* **PostgreSQL Connection**:
  Connects via `DATABASE_URL` (e.g. Render Hosted PostgreSQL) or individual environment variables (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`).
  ```bash
  $env:DATABASE_URL="postgresql://user:password@render-host.onrender.com/puc_bookstore"
  python server.py 8000
  ```

---

## 🔌 Key REST API Endpoints (`server.py`)

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/books` | Fetch all course textbooks with stock status | Public |
| `GET` | `/api/books/<id>` | Fetch detailed book information | Public |
| `POST` | `/api/login` | User authentication | Public |
| `POST` | `/api/register` | Student account registration | Public |
| `POST` | `/api/forgot-password` | Request password reset verification code | Public |
| `POST` | `/api/reset-password` | Submit new password with verification code | Public |
| `POST` | `/api/orders` | Create new order & generate 6-Digit Pickup PIN | Authenticated |
| `GET` | `/api/orders` | Fetch orders for current student | Authenticated |
| `GET` | `/api/orders/<id>` | Fetch specific order receipt & PIN token | Authenticated |

---

## 🛠️ Technology Stack

* **Frontend**: HTML5, Vanilla CSS3 (Custom PUC Design System), Modern JavaScript (ES6 Modules, Dynamic View Router), QRious (HTML5 Canvas QR Code Engine).
* **Backend Server**: Python REST API (`server.py`) & Database Adapter (`db_adapter.py`).
* **Database**: PostgreSQL (Render Cloud or Local PostgreSQL).
* **Security**: PBKDF2 SHA-256 Password Encryption (100,000 rounds), Session Token Authentication.
* **Typography**: Google Fonts (`Inter`, `Outfit`, `JetBrains Mono`).
* **Icons**: FontAwesome 6.4.0.

---

© 2026 Paññāsāstra University of Cambodia (PUC) - Digital Bookstore Project