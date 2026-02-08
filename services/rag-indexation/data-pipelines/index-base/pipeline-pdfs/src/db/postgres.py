import psycopg
import os

def get_connection():
    return psycopg.connect(
        host=os.getenv("PGVECTOR_HOST", "localhost"),
        port=os.getenv("PGVECTOR_PORT", 5432),
        dbname=os.getenv("PGVECTOR_DATABASE"),
        user=os.getenv("PGVECTOR_USER"),
        password=os.getenv("PGVECTOR_PASSWORD"),
        sslmode="disable",   # 👈 ESTA ES LA CLAVE
    )

