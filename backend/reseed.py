"""Recreate DB with updated schema and reseed demo data."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Ensure we run from the backend directory so SQLite path resolves correctly
os.chdir(os.path.dirname(__file__))

from app.database import engine, SessionLocal, Base
from app.data.seeder import seed_database

print("Creating all tables with latest schema...")
Base.metadata.create_all(bind=engine)
print("Tables created.")

db = SessionLocal()
try:
    seed_database(db)
finally:
    db.close()

print("\nDB fully reseeded.")
