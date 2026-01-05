from app.database import SessionLocal, Base, engine
from app.models import User
from app.jwt_helpers import pwd_context

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Create a new database session
db = SessionLocal()

# Replace these with the test credentials you want
email = "test@example.com"
password = "password123"

# Hash the password
hashed_password = pwd_context.hash(password)

# Create the user object
user = User(email=email, hashed_password=hashed_password)

# Add to the database
db.add(user)
db.commit()
db.refresh(user)

print(f"Test user created! ID: {user.id}, Email: {user.email}")

# Close the session
db.close()
