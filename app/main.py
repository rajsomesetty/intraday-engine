import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.dependency import get_db
from app.db.session import engine, SessionLocal
from app.services.execution_service import execute_trade
from app.services.risk_service import RiskException
from app.schemas.order import OrderRequest


# -----------------------------------
# Scheduler Setup
# -----------------------------------

scheduler = BackgroundScheduler()


def daily_reset_job():
    db = SessionLocal()
    try:
        db.execute(
            text("UPDATE account SET daily_pnl = 0 WHERE id=1")
        )
        db.commit()
        print("🔁 Daily PnL reset executed")
    except Exception as e:
        db.rollback()
        print("Daily reset failed:", e)
    finally:
        db.close()


# -----------------------------------
# Graceful Startup & Shutdown
# -----------------------------------

shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Intraday Engine starting up")

    # Schedule daily reset at midnight
    scheduler.add_job(
        daily_reset_job,
        trigger="cron",
        hour=0,
        minute=0,
    )

    scheduler.start()

    yield

    print("🛑 Intraday Engine shutting down...")

    shutdown_event.set()

    scheduler.shutdown(wait=False)

    engine.dispose()

    print("✅ Database connections closed")
    print("👋 Shutdown complete")


app = FastAPI(
    title="Intraday Equity Trading Engine",
    version="1.1.0",
    lifespan=lifespan
)


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
        raise HTTPException(status_code=503, detail="Database not ready")


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
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------------
# Admin Manual Reset
# -----------------------------------

@app.post("/admin/reset-day")
def reset_day(db: Session = Depends(get_db)):
    try:
        db.execute(
            text("UPDATE account SET daily_pnl = 0 WHERE id=1")
        )
        db.commit()
        return {"message": "Daily PnL reset successfully"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Reset failed")
