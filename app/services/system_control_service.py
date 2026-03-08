import redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

KILL_SWITCH_KEY = "global_trading_enabled"


def trading_enabled():
    """
    Returns True if trading is allowed.
    """

    try:
        value = r.get(KILL_SWITCH_KEY)

        if value is None:
            return True

        return value == "1"

    except Exception as e:

        print("❌ Kill switch check failed:", e)

        return True


def disable_trading():
    """
    Disable all trading globally.
    """

    try:

        r.set(KILL_SWITCH_KEY, "0")

        print("🛑 Global trading disabled")

    except Exception as e:

        print("❌ Failed to disable trading:", e)


def enable_trading():
    """
    Enable trading globally.
    """

    try:

        r.set(KILL_SWITCH_KEY, "1")

        print("✅ Global trading enabled")

    except Exception as e:

        print("❌ Failed to enable trading:", e)


# -----------------------------
# API COMPATIBILITY FUNCTIONS
# -----------------------------

def is_kill_switch_enabled():
    """
    Used by UI API.
    Returns True if trading is disabled.
    """

    return not trading_enabled()


def enable_kill_switch():
    """
    Enable kill switch → stop trading.
    """

    disable_trading()


def disable_kill_switch():
    """
    Disable kill switch → allow trading.
    """

    enable_trading()
