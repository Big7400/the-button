# run_dev_phase5.py
import webbrowser
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.models import User, Role, Product
from app.core.security import get_password_hash
from app.main import app
import uvicorn

# -----------------------
# Create DB + tables
# -----------------------
Base.metadata.create_all(bind=engine)

# -----------------------
# Seed dummy data
# -----------------------
def seed_data(db: Session):
    # Roles
    admin_role = Role(name="admin", description="Administrator")
    user_role = Role(name="user", description="Regular user")
    db.add_all([admin_role, user_role])
    db.commit()

    # Users
    admin = User(username="admin", email="admin@test.com", hashed_password=get_password_hash("admin123"), roles=[admin_role])
    user = User(username="user", email="user@test.com", hashed_password=get_password_hash("user123"), roles=[user_role])
    db.add_all([admin, user])

    # Products
    prod1 = Product(name="Laptop", description="High-end laptop", price=2000.0)
    prod2 = Product(name="Phone", description="Smartphone", price=1000.0)
    db.add_all([prod1, prod2])

    db.commit()
    print("✅ Seeded database with dummy users, roles, and products.")

# -----------------------
# Run server
# -----------------------
if __name__ == "__main__":
    with next(get_db()) as db:
        seed_data(db)
    webbrowser.open("http://127.0.0.1:8001/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
