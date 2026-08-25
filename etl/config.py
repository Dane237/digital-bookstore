import os

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'pass123')
DB_NAME = os.getenv('DB_NAME', 'puc_bookstore')

# Local Storage Configuration
OUTPUT_DIR = os.getenv('OUTPUT_DIR', os.path.join(os.path.dirname(__file__), 'output'))

# Pipeline Settings
USE_MOCK = os.getenv('USE_MOCK', 'false').lower() == 'true'
DEFAULT_EXTRACT_DAYS = 1

