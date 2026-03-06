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
