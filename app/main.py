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

from app.schemas.order import OrderRequest

from app.models.account import Account
from app.models.position import Position
from app.models.risk_config import RiskConfig
from app.api import backtest_routes
from app.services.strategy_engine import register_strategy
from app.strategies.moving_average_cross import MovingAverageCross
from app.api import strategy_analytics_routes

from app.services.metrics_service import (
    current_equity,
    current_exposure,
    kill_switch_state,
)

from app.api import risk_routes
from app.api import analytics_routes


# -----------------------------------
# Scheduler Setup
# -----------------------------------

scheduler = BackgroundScheduler()


# -----------------------------------
# Daily Reset Job
# -----------------------------------

def daily_reset_job():

    db = SessionLocal()

    try:

        db.execute(
            text("""
                UPDATE account
                SET daily_pnl = 0,
                    intraday_peak_equity = current_equity,
                    is_trading_enabled = TRUE,
                    breach_count = 0,
                    last_breach_reason = NULL,
                    last_breach_time = NULL
            """)
        )

        db.commit()

        print("🔁 Daily reset executed for all accounts")

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

        db.execute(
            text("""
                DELETE FROM equity_history
                WHERE created_at < now() - interval '30 days'
            """)
        )

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
# Graceful Startup & Shutdown
# -----------------------------------

shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("🚀 Intraday Engine starting up")

    # Register trading strategies
    register_strategy(MovingAverageCross("RELIANCE", account_id=1))
    register_strategy(MovingAverageCross("TCS", account_id=2))

    # Daily reset
    scheduler.add_job(
        daily_reset_job,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily_reset",
        replace_existing=True
    )

    # Cleanup old equity history
    scheduler.add_job(
        cleanup_equity_history,
        trigger="cron",
        hour=1,
        id="equity_cleanup",
        replace_existing=True
    )

    # MTM worker every 5 seconds
    scheduler.add_job(
        mtm_job,
        trigger="interval",
        seconds=5,
        id="mtm_worker",
        replace_existing=True
    )

    # Start market price listener
    listener_thread = threading.Thread(
        target=start_price_listener,
        daemon=True
    )

    listener_thread.start()

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
    version="1.6.0",
    lifespan=lifespan
)


# -----------------------------------
# Register Routers
# -----------------------------------

app.include_router(risk_routes.router)
app.include_router(analytics_routes.router)
app.include_router(backtest_routes.router)
app.include_router(strategy_analytics_routes.router)


# -----------------------------------
# Health Endpoints
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
# Risk Status Endpoint
# -----------------------------------

@app.get("/risk/status/{account_id}")
def risk_status(account_id: int, db: Session = Depends(get_db)):

    account = db.query(Account).filter(Account.id == account_id).first()

    risk_config = (
        db.query(RiskConfig)
        .filter(RiskConfig.account_id == account_id)
        .first()
    )

    positions = (
        db.query(Position)
        .filter(Position.account_id == account_id)
        .all()
    )

    if not account or not risk_config:

        raise HTTPException(
            status_code=500,
            detail="Risk system not initialized"
        )

    exposure = Decimal("0")
    open_positions = 0

    for pos in positions:

        qty = Decimal(pos.quantity)

        if qty > 0:

            open_positions += 1
            exposure += qty * Decimal(str(pos.average_price))

    # Update Prometheus metrics
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
        "risk_limits": {
            "max_allocation_pct": float(risk_config.max_allocation_pct),
            "max_exposure_pct": float(risk_config.max_exposure_pct),
            "daily_loss_limit": float(risk_config.daily_loss_limit),
            "max_open_positions": risk_config.max_open_positions,
        },
        "breach_info": {
            "breach_count": account.breach_count,
            "last_breach_reason": account.last_breach_reason,
            "last_breach_time": account.last_breach_time,
        }
    }


# -----------------------------------
# Prometheus Metrics Endpoint
# -----------------------------------

@app.get("/metrics")
def metrics():

    return Response(
        generate_latest(),
        media_type="text/plain"
    )


# -----------------------------------
# Order Execution
# -----------------------------------

@app.post("/orders")
def create_order(
    order: OrderRequest,
    db: Session = Depends(get_db),
):

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
            "idempotency_key": trade.order_idempotency_key,
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


# -----------------------------------
# Admin Manual Reset
# -----------------------------------

@app.post("/admin/reset-day")
def reset_day(db: Session = Depends(get_db)):

    try:

        db.execute(
            text("""
                UPDATE account
                SET daily_pnl = 0,
                    intraday_peak_equity = current_equity,
                    is_trading_enabled = TRUE,
                    breach_count = 0,
                    last_breach_reason = NULL,
                    last_breach_time = NULL
            """)
        )

        db.commit()

        return {"message": "Full intraday reset completed"}

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Reset failed"
        )
