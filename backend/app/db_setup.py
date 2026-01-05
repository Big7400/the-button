import psycopg2
from psycopg2 import sql

# --- 1. Database connection settings ---
DB_HOST = "localhost"        # Or your cloud DB host
DB_PORT = "5432"
DB_NAME = "thebuttonapp"
DB_USER = "your_db_username"
DB_PASSWORD = "your_db_password"

# --- 2. SQL statements for creating tables ---
create_tables = [
    """
    CREATE TABLE IF NOT EXISTS Users (
        user_id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        subscription_tier VARCHAR(50) DEFAULT 'Free',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS Markets (
        market_id SERIAL PRIMARY KEY,
        symbol VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100),
        type VARCHAR(50),
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS UserSettings (
        setting_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
        market_id INT REFERENCES Markets(market_id) ON DELETE CASCADE,
        timeframe VARCHAR(10) NOT NULL,
        indicators JSONB NOT NULL,
        trader_style VARCHAR(20) DEFAULT 'DayTrader',
        session_limits JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ScanResults (
        scan_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
        market_id INT REFERENCES Markets(market_id) ON DELETE CASCADE,
        timeframe VARCHAR(10) NOT NULL,
        status VARCHAR(10) DEFAULT 'PENDING',
        confidence NUMERIC(4,3) DEFAULT 0.0,
        reasons JSONB DEFAULT '[]',
        timestamp TIMESTAMP DEFAULT NOW()
    );
    """
]

# --- 3. Connect and create tables ---
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()

    for table in create_tables:
        cursor.execute(table)
        print("Table executed successfully!")

    cursor.close()
    conn.close()
    print("All tables created successfully!")

except Exception as e:
    print("Error creating tables:", e)
