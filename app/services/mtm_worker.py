import time
import logging
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.mtm_service import run_mtm_cycle

logging.basicConfig(level=logging.INFO)

SLEEP_INTERVAL = 1  # seconds


def mtm_loop():
    logging.info("Starting MTM Worker...")

    while True:
        db: Session = SessionLocal()

        try:
            run_mtm_cycle(db)

        except Exception as e:
            logging.error(f"MTM cycle failed: {e}")

        finally:
            db.close()

        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    mtm_loop()
