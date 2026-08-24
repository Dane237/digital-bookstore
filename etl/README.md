# 📊 PUC Bookstore ETL Pipeline

This pipeline extracts order and sales data from the **PostgreSQL** production database and uploads it to Amazon S3 in JSON Lines (`.jsonl`) format for analytics processing and data warehousing.

---

## ⚙️ Setup & Configuration

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   Create a `.env` file (see `.env.example`) and configure your PostgreSQL connection and S3 bucket details:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=puc_bookstore
   DB_USER=postgres
   DB_PASSWORD=yourpassword
   S3_BUCKET_NAME=your-s3-bucket-name
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
If you don't have a live PostgreSQL database or AWS credentials configured, you can still test the pipeline:
- **`USE_MOCK=true`**: Generates synthetic order data instead of querying the database.
- **Local Fallback**: If AWS credentials are not found, the script will save the `.jsonl` file to a temporary directory on your machine instead of failing, allowing you to inspect the output.

---

## 📂 S3 Output Partition Structure

Extracted data is formatted as JSON Lines and uploaded to S3 using hive-style date partitions for easy integration with AWS Athena or Spark:
```text
s3://{S3_BUCKET_NAME}/raw/orders/year=YYYY/month=MM/orders_extract_YYYYMMDD.json
```

---
© 2026 PUC Digital Bookstore - Academic Project
