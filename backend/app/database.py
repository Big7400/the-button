from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# CHANGE THIS ONLY IF YOUR DB DETAILS CHANGE
DATABASE_URL = "postgresql://stevitaylor@localhost:5432/thebuttonapp"

engine = create_engine(
    DATABASE_URL,
    echo=True  # logs SQL queries (VERY useful while building)
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
