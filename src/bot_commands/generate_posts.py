from telegram import Update
from ..repositories.pillow_repository import PillowRepository
from handlers.generate_posts_handler import GeneratePostsHandler
from telegram.ext import (
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)

ESPERANDO_LOGO = 1

async def crear_cartel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Perfecto! Vamos a preparar los carteles. 🖼️\n\nPor favor, envíame ahora la imagen del logo o envia /cancelar para abortar."
    )
    return ESPERANDO_LOGO

async def recibir_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    repository = PillowRepository()
    handler = GeneratePostsHandler(repository)
    
    foto_id = update.message.photo[-1].file_id
    archivo = await context.bot.get_file(foto_id)
    
    file_path = "shared/temporal_logo.jpg"
    await archivo.download_to_drive(file_path)
    
    await update.message.reply_text(
        f"¡Logo recibido y descargado como '{file_path}'! ✅\n\n(Procesando con Pillow...)"
    )
    
    handler.handle(file_path)
    
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operación cancelada. ¡Avísame cuando me necesites!")
    return ConversationHandler.END

post_handler = ConversationHandler(
    entry_points=[CommandHandler("crear_cartel", crear_cartel)],
    states={
        ESPERANDO_LOGO: [MessageHandler(filters.PHOTO, recibir_logo)]
    },
    fallbacks=[CommandHandler("cancelar", cancelar)]
)