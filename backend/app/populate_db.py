from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
import models

# Create tables if not exists (optional)
models.Base.metadata.create_all(bind=engine)

# Start session
db = SessionLocal()

# --- Add placeholder users ---
user1 = models.User(username="stevitaylor", email="steve@example.com", password_hash="hashedpassword")
user2 = models.User(username="testuser", email="test@example.com", password_hash="hashedpassword")
db.add_all([user1, user2])
db.commit()

# --- Add placeholder markets ---
market1 = models.Market(symbol="XAUUSD", name="Gold / USD")
market2 = models.Market(symbol="EURUSD", name="Euro / USD")
db.add_all([market1, market2])
db.commit()

# --- Add placeholder user settings ---
settings1 = models.UserSettings(user_id=user1.user_id, preference="dark_mode", value="true")
db.add(settings1)
db.commit()

# --- Add placeholder scanresults ---
scan1 = models.ScanResult(user_id=user1.user_id, market_id=market1.market_id,
                          timeframe="5m", status="PENDING", indicators={"MACD":0.0, "RSI":0.0}, confidence=0.0)
scan2 = models.ScanResult(user_id=user1.user_id, market_id=market2.market_id,
                          timeframe="15m", status="PENDING", indicators={"MACD":0.0, "RSI":0.0}, confidence=0.0)
db.add_all([scan1, scan2])
db.commit()

print("Database populated with placeholder data!")

db.close()
