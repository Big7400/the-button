from sqlalchemy import text
from backend.database import engine, Base
import models  # make sure all models are imported

print("🧨 Dropping all tables (using CASCADE)...")

with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE;"))
    conn.execute(text("CREATE SCHEMA public;"))
    conn.commit()

print("✅ All tables dropped successfully.")

print("🔧 Creating all tables...")
Base.metadata.create_all(bind=engine)
print("✅ All tables created successfully.")
