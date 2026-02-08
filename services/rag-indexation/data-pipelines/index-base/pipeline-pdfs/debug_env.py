import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

password = os.getenv("PGVECTOR_PASSWORD")
print(f"Password length: {len(password)}")
print(f"First char: {password[0]}")
print(f"Last char: {password[-1]}")
print(f"Raw repr: {repr(password)}")
