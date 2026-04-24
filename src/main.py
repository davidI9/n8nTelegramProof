import os
from dotenv import load_dotenv
from telegram.ext import Application

# Importamos nuestro handler ya empaquetado desde la carpeta comandos
from bot_commands.generate_posts import post_handler

def main():
    load_dotenv()
    
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(post_handler)
    
    # (Si en el futuro haces un comando /ayuda en otro archivo, harías esto:)
    # from comandos.ayuda import ayuda_handler
    # app.add_handler(ayuda_handler)

    print("🤖 Bot iniciado. Escribe /crear_cartel en Telegram...")
    app.run_polling()

if __name__ == '__main__':
    main()