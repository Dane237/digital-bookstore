import os

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'pass123')
DB_NAME = os.getenv('DB_NAME', 'puc_bookstore')

# AWS S3 Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'puc-bookstore-analytics-bucket')

# Pipeline Settings
USE_MOCK = os.getenv('USE_MOCK', 'false').lower() == 'true'
DEFAULT_EXTRACT_DAYS = 1
