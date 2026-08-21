# 📚 PUC Digital Bookstore - Mobile App (Android & iOS)

This part of the ecosystem contains the **Flutter** mobile application for Students, Staff, and Admins.

---

## 🚀 Key Features

### 🎓 For Students (Customers)
*   **Guest Browsing**: Search and filter course books by Department.
*   **Smart Cart**: Real-time stock verification.
*   **Secure Checkout**: Professional **Stripe Credit Card** payment flow.
*   **Digital Token**: Instant generation of a unique 6-digit **Pickup PIN** and **QR Code**.

### 🧑‍💼 For Staff & Admin
*   **Manager Dashboard**: Real-time business intelligence with **Revenue Trends**.
*   **Fulfillment Flow**: Professional 3-step workflow (Prepare -> Verify -> Release).
*   **Accountability**: Every fulfillment action is logged with the specific **Staff ID**.

---

## ⚙️ Deployment & Setup

### 1. Prerequisites
*   Backend API must be live (See root `backend/` folder).
*   Database tables must be created (See root `database/` folder).

### 2. Flutter Sync
1.  Update `baseUrl` in `lib/services/api_service.dart` to your Render service URL.
2.  Build for mobile: `flutter build apk --release`

---

## 🔐 Credentials for Demo

| Account Type | Email | Password |
| :--- | :--- | :--- |
| **Root Admin** | `admin@puc.edu.kh` | `pass123` |
| **Staff Member** | Create via Dashboard | Assign via Admin |

---
© 2026 PUC Digital Bookstore - Academic Project
