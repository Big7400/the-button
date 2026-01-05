#!/usr/bin/env python3
import os

# Define project structure
structure = {
    ".venv": None,
    "backend": {
        "__init__.py": "",
        "main.py": """from fastapi import FastAPI
from backend.api import users

app = FastAPI(title="TheButtonApp API")

# Include routers
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
def root():
    return {"status": "ok", "message": "API is alive"}
""",
        "models.py": """# backend/models.py
# Define your database models here
""",
        "api": {
            "__init__.py": "",
            "users.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "API is alive"}

@router.get("/")
def get_users():
    return {"users": ["Alice", "Bob", "Charlie"]}
"""
        },
    },
    "frontend": {},
    "docs": {},
    "README.md": "# TheButtonApp"
}

def create_structure(base_path, struct):
    for name, content in struct.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            # Create folder
            os.makedirs(path, exist_ok=True)
            # Recursively create inner structure
            create_structure(path, content)
        else:
            # Create file with content
            with open(path, "w") as f:
                f.write(content)
            print(f"Created file: {path}")

if __name__ == "__main__":
    base_dir = os.getcwd()
    create_structure(base_dir, structure)
    print("\n✅ Backend structure created successfully!")
    print("You can now run:\n")
    print("   source .venv/bin/activate")
    print("   python -m uvicorn backend.main:app --reload --port 8002")
