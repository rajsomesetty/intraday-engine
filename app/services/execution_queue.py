import redis
import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

r = redis.Redis(host=REDIS_HOST, port=6379)


def enqueue_execution(order):

    r.lpush(
        "execution_queue",
        json.dumps(order)
    )

def get_execution_queue_size():

    try:

        return r.llen("execution_queue")

    except Exception:

        return 0
