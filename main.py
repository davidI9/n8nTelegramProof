import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

# Cargamos las variables de entorno
load_dotenv()

app = FastAPI()

# Credenciales
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Inicializamos el cliente del Bot de Telegram
bot = Bot(token=BOT_TOKEN)

# Estructura esperada desde n8n
class N8nPayload(BaseModel):
    mensaje: str

@app.post("/n8n-webhook")
async def forward_to_telegram(payload: N8nPayload):
    try:
        # Usamos el método nativo de la librería para enviar el mensaje
        await bot.send_message(
            chat_id=CHAT_ID, 
            text=payload.mensaje,
            parse_mode="HTML" # Opcional: te permite enviar texto en negrita o cursiva desde n8n usando etiquetas <b>
        )
        return {"status": "ok", "info": "Mensaje entregado mediante python-telegram-bot"}
        
    except TelegramError as e:
        raise HTTPException(status_code=400, detail=f"Error de Telegram: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")