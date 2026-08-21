# 📚 PUC Digital Bookstore - Full-Stack Ecosystem

This repository contains the complete ecosystem for the **Paññāsāstra University of Cambodia (PUC)** Bookstore system. All applications (Mobile and Web) share the same **PostgreSQL** database via a central **FastAPI** backend.

---

## 📂 System Architecture (Separate Parts)

This project is divided into specialized folders to allow independent development of the Mobile and Web platforms:

1.  **[database/](./database)**: The "Single Source of Truth." Contains the SQL schema and table definitions shared by everyone.
2.  **[backend/](./backend)**: The central "Brain" (FastAPI). All platforms (Mobile and Web) connect to this API.
3.  **[etl/](./etl)**: Python data tools for managing and importing book inventory into the shared database.
4.  **[mobile_app/](./mobile_app)**: The Flutter mobile project for Android & iOS (includes Admin, Staff, and Customer features).
5.  **[web_app/](./web_app)**: Reserved for Web-based Staff and Customer portals.

---

## 🚀 Deployment Overview

### 1. Database (PostgreSQL)
Create a PostgreSQL instance on Render and run the script in `database/schema.sql`.

### 2. Backend (FastAPI)
Deploy the `backend/` folder to Render. Ensure the Environment Variables (`DB_HOST`, `STRIPE_KEY`, etc.) are configured.

### 3. Applications
- For Mobile details, see **[mobile_app/README.md](./mobile_app/README.md)**.
- For Web details, documentation will be added to the `web_app/` folder as development begins.

---
© 2026 PUC Digital Bookstore - Academic Project
