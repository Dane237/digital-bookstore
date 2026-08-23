import psycopg2
import logging
# noinspection PyUnresolvedReferences
from etl_pipeline import run_etl_pipeline
# noinspection PyUnresolvedReferences
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_test_data():
    """Inserts test records into the database for the ETL to extract."""
    if config.USE_MOCK:
        logging.info("USE_MOCK is True. Skipping database setup.")
        return False

    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        cursor = conn.cursor()

        # Insert a sample order for 'yesterday'
        logging.info("Inserting sample order into PostgreSQL...")
        
        insert_order = """
            INSERT INTO orders (user_id, total_amount, payment_method, pickup_pin, order_date) 
            VALUES (99, 120.00, 'Test Method', '123456', CURRENT_DATE - INTERVAL '1 day')
            RETURNING order_id
        """
        cursor.execute(insert_order)
        order_id = cursor.fetchone()[0]

        # Use valid book_id from seeded data or assume 1 for test
        insert_item = """
            INSERT INTO order_items (order_id, book_id, quantity, unit_price) 
            VALUES (%s, 1, 2, 60.00)
        """
        cursor.execute(insert_item, (order_id,))
        
        conn.commit()
        logging.info(f"Sample data inserted (Order ID: {order_id}).")
        return True

    except (psycopg2.Error, Exception) as e:
        logging.error(f"Failed to setup test data: {e}")
        logging.info("Make sure you have run schema.sql first and updated your .env file.")
        return False
    finally:
        try:
            # noinspection PyUnboundLocalVariable
            if 'cursor' in locals() and cursor:
                cursor.close()
            # noinspection PyUnboundLocalVariable
            if 'conn' in locals() and conn:
                conn.close()
        except NameError:
            pass

if __name__ == "__main__":
    logging.info("Starting End-to-End ETL Test...")
    
    # Optional: Setup real data if not in mock mode
    setup_test_data()
    
    # Run the actual pipeline
    run_etl_pipeline()
