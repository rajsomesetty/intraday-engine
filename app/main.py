import asyncio
from contextlib import asynccontextmanager
import threading

from apscheduler.schedulers.background import BackgroundScheduler

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response

from sqlalchemy.orm import Session
from sqlalchemy import text

from decimal import Decimal

from prometheus_client import generate_latest

from app.db.dependency import get_db
from app.db.session import engine, SessionLocal

from app.services.execution_service import execute_trade
from app.services.risk_service import RiskException
from app.services.rate_limit_service import RateLimitException

from app.services.mtm_service import run_mtm_cycle
from app.services.price_consumer import start_price_listener
from app.services.execution_worker import start_execution_worker
from app.services.strategy_worker import start_strategy_worker
from app.services.tick_worker import start_tick_worker

from app.schemas.order import OrderRequest

from app.models.account import Account
from app.models.position import Position

from app.services.strategy_engine import register_strategy
from app.strategies.moving_average_cross import MovingAverageCross

from app.api import backtest_routes
from app.api import strategy_analytics_routes
from app.api import strategy_status_routes
from app.api import risk_routes
from app.api import analytics_routes

from app.api import trade_routes
from app.api import position_routes
from app.api import system_routes
from app.api import system_status_routes
from app.api import system_health_routes
from app.api import ws_routes
from app.services.market_data_service import market_data_service

from app.services.metrics_service import (
    current_equity,
    current_exposure,
    kill_switch_state,
)

scheduler = BackgroundScheduler()
shutdown_event = asyncio.Event()


# -----------------------------------
# Worker Auto-Restart Wrapper
# -----------------------------------

def safe_worker(worker_func, name):

    while True:

        try:

            worker_func()

        except Exception as e:

            print(f"⚠️ {name} crashed:", e)
            print("🔁 Restarting worker...")


# -----------------------------------
# Daily Reset
# -----------------------------------

def daily_reset_job():

    db = SessionLocal()

    try:

        db.execute(text("""
            UPDATE account
            SET daily_pnl = 0,
                intraday_peak_equity = current_equity,
                is_trading_enabled = TRUE,
                breach_count = 0,
                last_breach_reason = NULL,
                last_breach_time = NULL
        """))

        db.commit()

        print("🔁 Daily reset executed")

    except Exception as e:

        db.rollback()
        print("❌ Daily reset failed:", e)

    finally:

        db.close()


# -----------------------------------
# Equity History Cleanup
# -----------------------------------

def cleanup_equity_history():

    db = SessionLocal()

    try:

        db.execute(text("""
            DELETE FROM equity_history
            WHERE created_at < now() - interval '30 days'
        """))

        db.commit()

        print("🧹 Equity history cleanup executed")

    except Exception as e:

        db.rollback()
        print("❌ Cleanup failed:", e)

    finally:

        db.close()


# -----------------------------------
# MTM Worker
# -----------------------------------

def mtm_job():

    db = SessionLocal()

    try:

        run_mtm_cycle(db)

    except Exception as e:

        print("❌ MTM cycle failed:", e)

    finally:

        db.close()


# -----------------------------------
# Startup Lifecycle
# -----------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("🚀 Intraday Engine starting up")

    # Initialize market prices
    market_data_service.update_price("RELIANCE", 500)

    print("📊 Initial price set: RELIANCE = 500")

    # -----------------------------------
    # Register Strategies
    # -----------------------------------

    register_strategy(
        MovingAverageCross(
            symbol="RELIANCE",
            account_id=1
        )
    )

    print("📈 Strategy registered: MovingAverageCross RELIANCE")

    # -----------------------------------
    # Scheduler Jobs
    # -----------------------------------

    scheduler.add_job(
        daily_reset_job,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily_reset",
        replace_existing=True
    )

    scheduler.add_job(
        cleanup_equity_history,
        trigger="cron",
        hour=1,
        id="equity_cleanup",
        replace_existing=True
    )

    scheduler.add_job(
        mtm_job,
        trigger="interval",
        seconds=60,
        id="mtm_worker",
        replace_existing=True
    )

    # -----------------------------------
    # Price Listener
    # -----------------------------------

    listener_thread = threading.Thread(
        target=start_price_listener,
        daemon=True
    )

    listener_thread.start()

    print("📡 Price listener started")

    # -----------------------------------
    # Tick Workers
    # -----------------------------------

    TICK_WORKERS = 2

    for _ in range(TICK_WORKERS):

        t = threading.Thread(
            target=safe_worker,
            args=(start_tick_worker, "tick_worker"),
            daemon=True
        )

        t.start()

    print(f"📊 {TICK_WORKERS} tick workers started")

    # -----------------------------------
    # Strategy Workers
    # -----------------------------------

    STRATEGY_WORKERS = 4

    for _ in range(STRATEGY_WORKERS):

        t = threading.Thread(
            target=safe_worker,
            args=(start_strategy_worker, "strategy_worker"),
            daemon=True
        )

        t.start()

    print(f"🧠 {STRATEGY_WORKERS} strategy workers started")

    # -----------------------------------
    # Execution Workers
    # -----------------------------------

    EXECUTION_WORKERS = 4

    for _ in range(EXECUTION_WORKERS):

        t = threading.Thread(
            target=safe_worker,
            args=(start_execution_worker, "execution_worker"),
            daemon=True
        )

        t.start()

    print(f"⚙️ {EXECUTION_WORKERS} execution workers started")

    scheduler.start()

    yield

    print("🛑 Intraday Engine shutting down...")

    shutdown_event.set()

    scheduler.shutdown(wait=False)

    engine.dispose()

    print("✅ Database connections closed")
    print("👋 Shutdown complete")


# -----------------------------------
# FastAPI App
# -----------------------------------

app = FastAPI(
    title="Intraday Equity Trading Engine",
    version="2.0.0",
    lifespan=lifespan
)


# -----------------------------------
# Routers
# -----------------------------------

app.include_router(risk_routes.router)
app.include_router(analytics_routes.router)
app.include_router(backtest_routes.router)
app.include_router(strategy_analytics_routes.router)
app.include_router(strategy_status_routes.router)

app.include_router(trade_routes.router)
app.include_router(position_routes.router)
app.include_router(system_routes.router)
app.include_router(system_status_routes.router)
app.include_router(system_health_routes.router)
app.include_router(ws_routes.router)


# -----------------------------------
# Health
# -----------------------------------

@app.get("/health/live")
def live():
    return {"status": "alive"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)):

    try:

        db.execute(text("SELECT 1"))

        return {"status": "ready"}

    except Exception:

        raise HTTPException(
            status_code=503,
            detail="Database not ready"
        )


# -----------------------------------
# Risk Status
# -----------------------------------

@app.get("/risk/status/{account_id}")
def risk_status(account_id: int, db: Session = Depends(get_db)):

    account = db.query(Account).filter(Account.id == account_id).first()

    positions = (
        db.query(Position)
        .filter(Position.account_id == account_id)
        .all()
    )

    if not account:

        raise HTTPException(
            status_code=500,
            detail="Account not initialized"
        )

    exposure = Decimal("0")
    open_positions = 0

    for pos in positions:

        qty = Decimal(pos.quantity)

        if qty > 0:

            open_positions += 1
            exposure += qty * Decimal(str(pos.entry_price))

    current_equity.set(float(account.current_equity))
    current_exposure.set(float(exposure))
    kill_switch_state.set(
        1 if account.is_trading_enabled else 0
    )

    return {
        "account_id": account_id,
        "equity": float(account.current_equity),
        "daily_pnl": float(account.daily_pnl),
        "exposure": float(exposure),
        "open_positions": open_positions,
        "trading_enabled": account.is_trading_enabled,
    }


# -----------------------------------
# Prometheus Metrics
# -----------------------------------

@app.get("/metrics")
def metrics():

    return Response(
        generate_latest(),
        media_type="text/plain"
    )


# -----------------------------------
# Manual Order
# -----------------------------------

@app.post("/orders")
def create_order(order: OrderRequest, db: Session = Depends(get_db)):

    try:

        trade = execute_trade(
            db=db,
            account_id=order.account_id,
            symbol=order.symbol,
            quantity=order.quantity,
            price=order.price,
            side=order.side,
            idempotency_key=order.idempotency_key,
        )

        return {
            "id": trade.id,
            "symbol": trade.symbol,
            "quantity": trade.quantity,
            "price": trade.entry_price,
            "status": trade.status,
        }

    except RiskException as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except RateLimitException as e:

        raise HTTPException(
            status_code=429,
            detail=str(e)
        )
