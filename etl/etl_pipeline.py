import os
import json
import logging
# noinspection PyPackageRequirements
import psycopg2
# noinspection PyPackageRequirements
from psycopg2.extras import RealDictCursor
# noinspection PyPackageRequirements
import boto3
import tempfile
from datetime import datetime, timedelta, timezone
# noinspection PyPackageRequirements
from botocore.exceptions import ClientError
# noinspection PyPackageRequirements
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

# Import configuration after loading environment variables
# noinspection PyUnresolvedReferences
import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_etl_pipeline():
    logging.info(f"Starting ETL extraction for database: {config.DB_NAME}")

    # Define extraction window
    target_date = (datetime.now(timezone.utc) - timedelta(days=config.DEFAULT_EXTRACT_DAYS)).strftime('%Y-%m-%d')
    logging.info(f"Extracting orders on or after: {target_date}")

    if config.USE_MOCK:
        logging.info("Running in MOCK mode. Generating sample data...")
        rows = [
            {"order_id": 101, "user_id": 1, "total_amount": 59.99, "payment_method": "Credit Card", "created_at": target_date, "book_id": 10, "quantity": 1, "price": 59.99},
            {"order_id": 102, "user_id": 2, "total_amount": 25.50, "payment_method": "PayPal", "created_at": target_date, "book_id": 15, "quantity": 1, "price": 25.50},
        ]
        process_data(rows, target_date)
        return

    conn = None
    cursor = None
    try:
        # Connect to PostgreSQL Database
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query completed orders and their items
        query = """
            SELECT O.order_id, O.user_id, O.total_amount, O.payment_method,
            O.order_date as created_at, OI.book_id, OI.quantity, OI.unit_price as price
            FROM orders O
            JOIN order_items OI ON O.order_id = OI.order_id
            WHERE CAST(O.order_date AS DATE) = %s
        """
        cursor.execute(query, (target_date,))
        rows = cursor.fetchall()

        if not rows:
            logging.info("No new order data found for the specified date.")
            return

        process_data(rows, target_date)

    except psycopg2.Error as db_err:
        logging.error(f"Database error occurred: {db_err}")
        logging.info("Tip: Check your DB_PASSWORD in etl/.env or set USE_MOCK=true to test.")
    except ClientError as s3_err:
        logging.error(f"AWS S3 error occurred: {s3_err}")
    except Exception as e:
        logging.error(f"Unexpected error in ETL execution: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
            logging.info("PostgreSQL connection closed.")

def process_data(rows, target_date):
    # Transform rows into JSON Lines format
    json_data = "\n".join([json.dumps(row, default=str) for row in rows])

    file_name = f"orders_extract_{target_date.replace('-', '')}.json"
    
    # Use tempfile for cross-platform compatibility
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_f:
        temp_f.write(json_data)
        local_file_path = temp_f.name

    s3_key = f"raw/orders/year={target_date[:4]}/month={target_date[5:7]}/{file_name}"
    try:
        # Load data into Amazon S3
        s3_client = boto3.client('s3')
        logging.info(f"Uploading {file_name} to S3 bucket: {config.S3_BUCKET_NAME}...")
        s3_client.upload_file(local_file_path, config.S3_BUCKET_NAME, s3_key)
        logging.info("ETL pipeline executed successfully. Data loaded to S3.")
    except Exception as e:
        if "Unable to locate credentials" in str(e):
            logging.warning("AWS credentials not found. Skipping S3 upload.")
            logging.info(f"Local file saved at: {local_file_path} (would have been uploaded to s3://{config.S3_BUCKET_NAME}/{s3_key})")
            return
        logging.error(f"Error during S3 processing: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(local_file_path):
            os.remove(local_file_path)

if __name__ == "__main__":
    run_etl_pipeline()
