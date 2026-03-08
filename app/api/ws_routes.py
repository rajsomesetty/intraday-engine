from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis
import os
import asyncio

router = APIRouter()

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    decode_responses=True
)


@router.websocket("/ws/trades")
async def trade_stream(websocket: WebSocket):

    await websocket.accept()

    pubsub = redis_client.pubsub()
    pubsub.subscribe("trade_events")

    try:

        while True:

            message = pubsub.get_message()

            if message and message["type"] == "message":

                await websocket.send_text(message["data"])

            await asyncio.sleep(0.01)

    except WebSocketDisconnect:

        print("🔌 WebSocket client disconnected")

    except Exception as e:

        print("⚠️ WebSocket error:", e)

    finally:

        pubsub.close()
