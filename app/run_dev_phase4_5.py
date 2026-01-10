#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from app.database import SessionLocal, engine, Base
from app.models import User, Role, Product, Order
from app.core.security import get_password_hash
import psutil

PORT = 8001

def kill_port(port):
    """Kill processes using the port to avoid conflicts"""
    for proc in psutil.process_iter(['pid', 'name']):
        for conn in proc.connections(kind='inet'):
            if conn.laddr.port == port:
                print(f"Killing process {proc.info['pid']} ({proc.info['name']}) on port {port}")
                proc.kill()

def seed_db():
    """Seed the database with roles, users, products, and orders"""
    db = SessionLocal()

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
            hashed_password=get_password_hash("AdminPass123"),
            role_id=admin_role.id
        )
        db.add(admin_user)

    if not db.query(User).filter_by(email="user@example.com").first():
        normal_user = User(
            email="user@example.com",
            hashed_password=get_password_hash("UserPass123"),
            role_id=user_role.id
        )
        db.add(normal_user)

    # Products
    if not db.query(Product).first():
        products = [
            Product(name="Product A", description="First product", price=19.99),
            Product(name="Product B", description="Second product", price=29.99),
        ]
        db.add_all(products)

    # Orders
    if not db.query(Order).first():
        order1 = Order(user_id=normal_user.id, product_id=products[0].id, quantity=2)
        order2 = Order(user_id=normal_user.id, product_id=products[1].id, quantity=1)
        db.add_all([order1, order2])

    db.commit()
    db.close()
    print("Database seeding complete ✅")

def run_server():
    """Run Uvicorn server with live reload"""
    print("Starting server on port", PORT)
    subprocess.run(["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", str(PORT)])

if __name__ == "__main__":
    print("=== Phase 4.5 Dev Runner ===")
    
    # Step 1: Kill existing processes on port
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil

    kill_port(PORT)

    # Step 2: Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Step 3: Seed database
    seed_db()

    # Step 4: Start server
    run_server()
