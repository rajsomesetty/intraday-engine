from sqlalchemy import text
from sqlalchemy.orm import Session


class RateLimitException(Exception):
    pass


def enforce_rate_limit(db: Session, account_id: int):

    # orders last second
    last_second = db.execute(
        text("""
        SELECT count(*)
        FROM order_rate_limit
        WHERE account_id=:id
        AND created_at > now() - interval '1 second'
        """),
        {"id": account_id}
    ).scalar()

    if last_second >= 5:
        raise RateLimitException("Order rate limit exceeded (1 sec)")

    # orders last minute
    last_minute = db.execute(
        text("""
        SELECT count(*)
        FROM order_rate_limit
        WHERE account_id=:id
        AND created_at > now() - interval '1 minute'
        """),
        {"id": account_id}
    ).scalar()

    if last_minute >= 100:
        raise RateLimitException("Order rate limit exceeded (1 min)")

    # record order
    db.execute(
        text("""
        INSERT INTO order_rate_limit(account_id)
        VALUES (:id)
        """),
        {"id": account_id}
    )
