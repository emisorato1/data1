import psycopg
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

host = os.getenv("PGVECTOR_HOST", "127.0.0.1")
port = os.getenv("PGVECTOR_PORT", "5432")
dbname = os.getenv("PGVECTOR_DATABASE", "eai_platform")
user = os.getenv("PGVECTOR_USER", "postgres")
password = os.getenv("PGVECTOR_PASSWORD", "postgres")

print(f"Connecting to {host}:{port} as {user}...")

try:
    with psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        autocommit=True,
        sslmode="disable"
    ) as conn:
        print("✅ Connection successful!")
        print(conn.execute("SELECT version()").fetchone())
except Exception as e:
    print(f"❌ Connection failed: {e}")
