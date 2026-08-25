# 📊 PUC Bookstore ETL Pipeline

This pipeline extracts order and sales data from the **PostgreSQL** production database and exports it to local storage in JSON Lines (`.jsonl`) format (`etl/output/`) for analytics processing and data warehousing.

---

## ⚙️ Setup & Configuration

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   Create a `.env` file (see `.env.example`) and configure your PostgreSQL connection and output directory:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=puc_bookstore
   DB_USER=postgres
   DB_PASSWORD=yourpassword
   OUTPUT_DIR=output
   USE_MOCK=false
   ```

3. **Database Schema**:
   Ensure PostgreSQL tables are initialized using `database/schema.sql`.

---

## 🚀 Running the Pipeline

To run the ETL extraction pipeline manually:
```bash
python etl_pipeline.py
```

### 🧪 Mock & Development Mode
If you don't have a live PostgreSQL database running, you can test the pipeline using mock data:
- **`USE_MOCK=true`**: Generates synthetic order data instead of querying the database and saves it directly to `output/orders_extract_YYYYMMDD.jsonl`.

---

## 📂 Output File Structure

Extracted data is formatted as JSON Lines (`.jsonl`) and stored in the local output directory (`etl/output/`):
```text
etl/output/orders_extract_YYYYMMDD.jsonl
```

---
© 2026 PUC Digital Bookstore - Academic Project

