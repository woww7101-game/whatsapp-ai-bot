import os
import logging

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")


@app.get("/")
async def home():
    return {"status": "WhatsApp bot is running"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN and challenge is not None:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)


async def send_whatsapp_message(to: str, message: str):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        logger.error("WhatsApp credentials are missing in environment variables")
        return

    url = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

        if response.is_success:
            logger.info("WhatsApp reply sent successfully")
        else:
            # Не выводим токен или заголовки авторизации в логи.
            logger.error(
                "WhatsApp API error: HTTP %s; response: %s",
                response.status_code,
                response.text[:1000],
            )


@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()

    logger.info("WhatsApp webhook received")

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") != "messages":
                    continue

                value = change.get("value", {})
                messages = value.get("messages", [])

                for message in messages:
                    # Отвечаем только на текстовые сообщения.
                    if message.get("type") != "text":
                        continue

                    sender = message.get("from")
                    text = message.get("text", {}).get("body", "")

                    if not sender or not text:
                        continue

                    logger.info("Incoming text message received")

                    await send_whatsapp_message(
                        sender,
                        "Привет! 👋 Я получил твоё сообщение. Скоро здесь появится ИИ-помощник!",
                    )

    except Exception:
        logger.exception("Error processing WhatsApp webhook")

    # Meta должна получить быстрый успешный ответ на Webhook.
    return {"status": "ok"}
