import subprocess
import sys
import os
import time
import webbrowser
from app.database import SessionLocal, engine, Base
from app.models import User, Role, Product, Order
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

PORT = 8001
URL = f"http://127.0.0.1:{PORT}/docs"

def git_commit():
    """Stage all changes and commit with a user prompt."""
    print("=== Git Commit Helper ===")
    commit_msg = input("Enter commit message (or leave blank to skip commit): ").strip()
    if commit_msg:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print("Changes committed.")
    else:
        print("Skipping commit.")

def is_port_in_use(port):
    """Check if port is in use by a Python process."""
    result = subprocess.run(
        ["lsof", "-i", f":{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip() != ""

def kill_python_on_port(port):
    """Kill only Python processes using the port (safe on macOS)."""
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"],
        stdout=subprocess.PIPE,
        text=True
    )
    pids = result.stdout.strip().split("\n")
    for pid in pids:
        if pid:
            # check process name
            name = subprocess.run(
                ["ps", "-p", pid, "-o", "comm="],
                stdout=subprocess.PIPE,
                text=True
            ).stdout.strip()
            if "Python" in name:
                print(f"Killing Python process {pid} on port {port}")
                subprocess.run(["kill", "-9", pid])

def seed_database():
    """Create roles, users, products, orders for testing."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # Roles
    admin_role = db.query(Role).filter_by(name="admin").first()
    user_role = db.query(Role).filter_by(name="user").first()
    if not admin_role:
        admin_role = Role(name="admin")
        db.add(admin_role)
    if not user_role:
        user_role = Role(name="user")
        db.add(user_role)
    db.commit()

    # Users
    if not db.query(User).filter_by(email="admin@example.com").first():
        admin_user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role_id=admin_role.id
        )
        db.add(admin_user)
    if not db.query(User).filter_by(email="user@example.com").first():
        regular_user = User(
            email="user@example.com",
            hashed_password=get_password_hash("user123"),
            role_id=user_role.id
        )
        db.add(regular_user)
    db.commit()

    # Products
    if db.query(Product).count() == 0:
        products = [
            Product(name="Product A", description="Sample product A", price=9.99),
            Product(name="Product B", description="Sample product B", price=19.99),
        ]
        db.add_all(products)
        db.commit()

    # Orders
    if db.query(Order).count() == 0:
        order = Order(user_id=regular_user.id, product_id=products[0].id, quantity=2)
        db.add(order)
        db.commit()

    db.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    print("=== Super Dev Runner (Phase 4.5) ===")

    # Step 1: Commit changes
    git_commit()

    # Step 2: Kill Python on port
    if is_port_in_use(PORT):
        kill_python_on_port(PORT)
        time.sleep(1)

    # Step 3: Seed database
    seed_database()

    # Step 4: Start FastAPI server
    print("Starting FastAPI server...")
    subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", str(PORT)])

    # Step 5: Open browser automatically
    time.sleep(2)
    print(f"Opening {URL} in browser...")
    webbrowser.open(URL)

    print("=== Dev Environment Ready ===")
