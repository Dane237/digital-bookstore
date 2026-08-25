# 🌐 PUC Digital Bookstore — Customer Web Application

Official Web Application platform for **Paññāsāstra University of Cambodia (PUC)** digital campus bookstore system, designed exclusively for **Student Customers**.

🌐 **Live Storefront Deployment**: [https://unrivaled-piroshki-69f896.netlify.app/](https://unrivaled-piroshki-69f896.netlify.app/)

---

## 📂 Architecture Overview

The web application is located in **[`customer/`](./customer)** as a full-stack Single Page Application (SPA) providing the **Student Customer Storefront**.

| Directory | Description | Status | Live URL |
| :--- | :--- | :--- | :--- |
| **[`customer/`](./customer)** | Customer Web Application for **Student Customers**. Features course catalog search, shopping cart, checkout (Stripe/ABA/Card), 6-Digit Pickup PIN & QR token generation, and personal order tracking (`My Orders`). | 🚀 Production Ready | [Netlify App](https://unrivaled-piroshki-69f896.netlify.app/) |


> [!NOTE]
> **Staff & Admin Functionality**: The Web Application is strictly for student customers. Counter staff and administrators perform order fulfillment, 6-digit PIN verification, stock management, and sales monitoring using the **Flutter Mobile App** ([`mobile_app/`](../mobile_app/README.md)) and **Staff Terminal CLI** ([`backend/`](../backend/README.md)).

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
👉 **[https://unrivaled-piroshki-69f896.netlify.app/](https://unrivaled-piroshki-69f896.netlify.app/)**

---

## 🔑 Key Features & System Capabilities

1. **Student Customer Storefront**:
   - Academic Course Search & Department filtering chips.
   - Interactive book details with quantity steppers and real-time stock pills.
   - Session shopping cart with live total calculations.
   - Mandatory student authentication with **PBKDF2 SHA-256** password hashing.
   - Multi-step checkout with Stripe, ABA KHQR Mobile Banking, and Direct Card payment options.
   - Instant Digital Receipt with unique **6-Digit Pickup PIN** & HTML5 Canvas QR code.
   - Student order tracking (`My Orders`) and store pickup instructions.

2. **Database Compatibility**:
   - Dual database adapter (`db_adapter.py`) supporting Render Hosted **PostgreSQL** and local **SQLite3**.

---

## 🛠️ Technology Stack

* **Frontend**: HTML5, Vanilla CSS3 (Custom PUC Design System), Modern JavaScript (ES6 Modules & Dynamic Router), QRious Canvas QR Engine.
* **Backend Server**: Python REST API (`server.py`) & Database Adapter (`db_adapter.py`).
* **Database**: PostgreSQL (Render Hosted) / SQLite3 (Local fallback).
* **Security**: PBKDF2 SHA-256 Password Encryption.

---

## 📖 Detailed Documentation

For full technical specifications, UI workflow screen breakdowns, database setup, and detailed API documentation, please refer to:  
👉 **[web_app/customer/README.md](./customer/README.md)**

---

© 2026 Paññāsāstra University of Cambodia (PUC) - Digital Bookstore Project

