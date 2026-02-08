import os
from dotenv import load_dotenv

# Si config.py y .env están en la misma carpeta 'config/'
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')

load_dotenv(env_path, override=True)

DB_CONFIG = {
    'server': os.getenv('SERVER'),
    'database': os.getenv('DATABASE'),
    'user': os.getenv('USER'),
    'password': os.getenv('PASSWORD'),
    'driver': os.getenv('DB_DRIVER')
}

PIPELINE_SETTINGS = {
    'bronze_dir': 'data/1_bronze',
    'silver_dir': 'data/2_silver',
    'gold_dir': 'data/3_gold',
    'default_start_date': "2024-01-01 00:00:00"
}