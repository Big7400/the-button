from datetime import datetime
from backend.database import SessionLocal
from models import User, Scan
import yfinance as yf
import ccxt

# --- CONFIG ---
USERS_TO_SCAN = ["stevi"]  # usernames to attach scans to
MARKETS = {
    "EUR/USD": "forex",
    "GBP/JPY": "forex",
    "XAU/USD": "metal",       # gold
    "SPY": "index",
    "BTC/USDT": "crypto"
}

# --- INIT ---
db = SessionLocal()

# Get user IDs
users = db.query(User).filter(User.username.in_(USERS_TO_SCAN)).all()
user_map = {u.username: u.id for u in users}

# Setup CCXT exchange for forex/crypto
exchange = ccxt.binance({'enableRateLimit': True})

# --- SCAN LOGIC ---
def fetch_price(symbol, market_type):
    if market_type in ["forex", "crypto"]:
        ohlcv = exchange.fetch_ticker(symbol)
        return ohlcv['last']  # last traded price
    elif market_type in ["index", "metal"]:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        return float(data['Close'][-1])
    else:
        return None

def run_scan_for_user(user_id):
    for symbol, market_type in MARKETS.items():
        price = fetch_price(symbol, market_type)
        scan = Scan(
            input_text=symbol,
            result=str(price),
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        db.add(scan)
    db.commit()

# --- RUN SCANS ---
for username, user_id in user_map.items():
    print(f"Running scans for {username}...")
    run_scan_for_user(user_id)

print("✅ All scans completed.")
