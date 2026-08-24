# 📚 PUC Digital Bookstore - Full-Stack Ecosystem

This repository contains the complete ecosystem for the **Paññāsāstra University of Cambodia (PUC)** Bookstore system. All applications (Mobile App and Web Application) share the same **PostgreSQL** database via central API services.

🌐 **Live Web Customer Storefront**: [https://charming-rugelach-827e8e.netlify.app/](https://charming-rugelach-827e8e.netlify.app/)

---

## 📂 System Architecture (Separate Parts)

This project is divided into specialized folders to allow independent development across platforms:

1.  **[database/](./database)**: The "Single Source of Truth." Contains the PostgreSQL schema and table definitions shared by all applications.
2.  **[backend/](./backend)**: Central FastAPI backend service connecting clients to PostgreSQL. Includes the **Staff Terminal CLI** for order fulfillment.
3.  **[etl/](./etl)**: Python ETL pipeline extracting order data from PostgreSQL to Amazon S3 for analytics.
4.  **[mobile_app/](./mobile_app)**: Flutter mobile application for Android & iOS (supports **Student Customers**, **Staff**, and **Admins**).
5.  **[web_app/](./web_app)**: Web Application hub containing the full-stack Web Application ([`web_app/customer/`](./web_app/customer)), featuring both the **Student Customer Storefront** and the **Staff Manager Control Center**.

---

## 🚀 Deployment Overview

### 1. Database (PostgreSQL)
Create a PostgreSQL instance (e.g., Render Hosted PostgreSQL) and run the initialization script in `database/schema.sql`.

### 2. Backend API
Deploy the `backend/` FastAPI folder to Render, or launch the Python REST API server in `web_app/customer/server.py`. Ensure Environment Variables (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `STRIPE_KEY`, etc.) are configured.

### 3. Applications
- **Mobile (Flutter)**: See **[mobile_app/README.md](./mobile_app/README.md)** (Customer, Staff & Admin features).
- **Web Application**: Live on **[Netlify](https://charming-rugelach-827e8e.netlify.app/)**. See **[web_app/README.md](./web_app/README.md)** and **[web_app/customer/README.md](./web_app/customer/README.md)** (Customer Storefront & Staff Manager Control Center).

---

© 2026 PUC Digital Bookstore - Academic Project
