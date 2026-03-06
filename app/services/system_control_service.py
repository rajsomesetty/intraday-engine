import redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379)


KILL_SWITCH_KEY = "global_trading_enabled"


def trading_enabled():

    try:

        value = r.get(KILL_SWITCH_KEY)

        if value is None:
            return True

        return value.decode() == "1"

    except Exception as e:

        print("❌ Kill switch check failed:", e)

        return True


def disable_trading():

    try:

        r.set(KILL_SWITCH_KEY, "0")

        print("🛑 Global trading disabled")

    except Exception as e:

        print("❌ Failed to disable trading:", e)


def enable_trading():

    try:

        r.set(KILL_SWITCH_KEY, "1")

        print("✅ Global trading enabled")

    except Exception as e:

        print("❌ Failed to enable trading:", e)
