# 🌐 PUC Digital Bookstore — Web Application Hub

Official Web Application platform for **Paññāsāstra University of Cambodia (PUC)** digital campus bookstore system.

🌐 **Live Storefront Deployment**: [https://unrivaled-piroshki-69f896.netlify.app/](https://unrivaled-piroshki-69f896.netlify.app/)

---

## 📂 Architecture Overview

The web application is located in **[`customer/`](./customer)** as a full-stack Single Page Application (SPA) integrating both the **Student Customer Storefront** and the **Staff Manager Control Center**.

| Directory | Description | Status | Live URL |
| :--- | :--- | :--- | :--- |
| **[`customer/`](./customer)** | Unified Web Application containing both the **Student Customer Storefront** and the **Staff Manager Dashboard**. Features course search, cart, checkout (Stripe/ABA/Card), 6-Digit Pickup PIN / QR generation, order tracking, sales analytics, PIN verification, and stock control. | 🚀 Production Ready | [Netlify App](https://unrivaled-piroshki-69f896.netlify.app/) |
| **[`staff/`](./staff)** | Legacy Standalone Staff directory. | ℹ️ Integrated into `customer/` & `mobile_app/` | N/A |

> [!NOTE]
> **Staff & Admin Functionality**: Staff and Admin features (order fulfillment, 6-digit PIN verification, stock management, and sales metrics) are fully integrated into the Web App Manager Dashboard (`web_app/customer/` via `#manager-dashboard`) as well as the **Flutter Mobile App** ([`mobile_app/`](../mobile_app/README.md)).

---

## 🚀 Quick Start Guide

To launch the Web Application locally:

```bash
# 1. Navigate to the web app customer directory
cd web_app/customer

# 2. Launch the development server
python server.py 8000
```

Once started, open your browser and navigate to:  
👉 **`http://localhost:8000`**

Or visit the live production app at:  
👉 **[https://charming-rugelach-827e8e.netlify.app/](https://unrivaled-piroshki-69f896.netlify.app/)**

---

## 🔑 Key Features & System Capabilities

1. **Student Customer Storefront**:
   - Academic Course Search & Department filtering chips.
   - Interactive book details with quantity steppers and real-time stock pills.
   - Session shopping cart with live total calculations.
   - Mandatory student authentication with **PBKDF2 SHA-256** password hashing.
   - Multi-step checkout with Stripe, ABA KHQR Mobile Banking, and Direct Card payment options.
   - Instant Digital Receipt with unique **6-Digit Pickup PIN** & HTML5 Canvas QR code.
   - Student order tracking (`My Orders`) and pickup instructions.

2. **Staff Manager Control Center**:
   - Manager Dashboard (`#manager-dashboard`) accessible to staff accounts.
   - Real-time sales analytics (Total Revenue, Business Worth, Total Orders).
   - Interactive 6-Digit PIN verification tool & QR scanner modal.
   - 3-step order fulfillment pipeline (`Pending` ➔ `Ready for Pickup` ➔ `Picked Up`).
   - Staff account registration modal & inventory stock management.

3. **Database Compatibility**:
   - Dual database adapter (`db_adapter.py`) supporting Render Hosted **PostgreSQL** and local **SQLite3**.

---

## 🛠️ Technology Stack

* **Frontend**: HTML5, Vanilla CSS3 (Custom PUC Design System), Modern JavaScript (ES6 Modules & Dynamic Router), QRious Canvas QR Engine.
* **Backend Server**: Python REST API (`server.py`) & Database Adapter (`db_adapter.py`).
* **Database**: PostgreSQL (Render Hosted) / SQLite3 (Local fallback).
* **Security**: PBKDF2 SHA-256 Password Encryption & Role-Based Access Control.

---

## 📖 Detailed Documentation

For full technical specifications, 13 UI workflow screen breakdowns, database setup, and detailed API documentation, please refer to:  
👉 **[web_app/customer/README.md](./customer/README.md)**

---

© 2026 Paññāsāstra University of Cambodia (PUC) - Digital Bookstore Project
