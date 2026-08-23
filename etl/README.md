# PUC Bookstore ETL Pipeline

This pipeline extracts order data from the MySQL production database and uploads it to Amazon S3 as JSON Lines format for analytics processing.

## Setup

1.  **Dependencies**: Install the required Python packages.
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**: Create a `.env` file (see `.env.example`) and add your database credentials and S3 bucket name.

3.  **Database**: If you haven't set up the tables yet, run the `schema.sql` script in your MySQL instance.
    ```bash
    mysql -u root -p < schema.sql
    ```

## Running the Pipeline

To run the pipeline manually:
```bash
python etl_pipeline.py
```

### Mock Mode
If you want to test the transformation and S3 upload without a live MySQL database, set `USE_MOCK=true` in your `.env` file.

## Output Structure
Data is uploaded to S3 with the following partition structure:
`s3://{BUCKET_NAME}/raw/orders/year=YYYY/month=MM/orders_extract_YYYYMMDD.json`
