import os

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()

VERIFY_TOKEN = os.getenv(
    "WHATSAPP_VERIFY_TOKEN",
    "my_verify_token"
)


@app.get("/")
async def home():
    return {"status": "WhatsApp bot is running"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("=== WEBHOOK VERIFICATION ===")
    print(f"Mode received: {mode!r}")
    print(f"Token received: {'present' if token else 'missing'}")
    print(f"Challenge received: {challenge!r}")
    print(f"Expected token configured: {bool(VERIFY_TOKEN)}")
    print(f"Token matches: {token == VERIFY_TOKEN}")

    if mode == "subscribe" and token == VERIFY_TOKEN and challenge is not None:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()

    print("WhatsApp webhook received:")
    print(data)

    return {"status": "ok"}
