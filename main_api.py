import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from config import Config

app = FastAPI(title="AuraGuard Core Event Engine")

@app.get("/health")
def health_check():
    return {"status": "operational", "compliance": "UK-GDPR / Caldicott-Compliant"}

@app.websocket("/ws/telemetry")
async def telemetry_stream(websocket: WebSocket):
    await websocket.accept()
    redis_client = aioredis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(Config.STREAM_CHANNEL, Config.ALERT_CHANNEL)
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                data = json.loads(message["data"])
                data["event_source"] = message["channel"]
                await websocket.send_json(data)
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        await pubsub.unsubscribe()
        await redis_client.close()
