-- ==========================
-- Intraday Engine DB Schema
-- ==========================

-- Drop existing tables (dev only)
DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS positions CASCADE;

-- ==========================
-- Trades Table
-- ==========================

CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    order_idempotency_key VARCHAR(255) NOT NULL UNIQUE,
    symbol VARCHAR(255),
    quantity INTEGER,
    entry_price FLOAT,
    exit_price FLOAT,
    pnl FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_trades_symbol ON trades(symbol);


-- ==========================
-- Positions Table
-- ==========================

CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(255) NOT NULL UNIQUE,
    quantity INTEGER DEFAULT 0,
    average_price FLOAT DEFAULT 0.0
);

CREATE INDEX ix_positions_symbol ON positions(symbol);

-- ==========================
-- End of Schema
-- ==========================
