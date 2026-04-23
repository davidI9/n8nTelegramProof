from telegram import Update
from ..repositories.pillow_repository import PillowRepository
from handlers.generate_posts_handler import GeneratePostsHandler
from ..dtos.generate_template_dto import GenerateTemplateDTO
from telegram.ext import (
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)

ESPERANDO_LOGO = 1
ESPERANDO_FIRST_LINE = 2
ESPERANDO_SECOND_LINE = 3
ESPERANDO_DATE = 4

async def crear_cartel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Perfecto! Vamos a preparar los carteles. 🖼️\n\nLa descripción de los carteles tienen 2 líneas, enviame la primera de ellas porfavor."
    )
    context.user_data['template_dto'] = GenerateTemplateDTO(
        script_path="/src/shared/create-project.sh",
        activity_type=1,
        speakers=0,
        first_line="",
        second_line="",
        event_date=None
    )
    return ESPERANDO_FIRST_LINE

async def get_first_line(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dto: GenerateTemplateDTO = context.user_data['template_dto']
    dto.first_line = update.message.text
    await update.message.reply_text(
        "¡Genial! Ahora envíame la segunda línea de la descripción."
    )
    return ESPERANDO_SECOND_LINE

async def get_second_line(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dto: GenerateTemplateDTO = context.user_data['template_dto']
    dto.second_line = update.message.text
    await update.message.reply_text(
        "¡Perfecto! Por último, envíame la fecha y hora del evento en formato YYYYMMDD HHMM."
    )
    return ESPERANDO_DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dto: GenerateTemplateDTO = context.user_data['template_dto']
    
    
    
    try:
        dto.event_date = update.message.text
        await update.message.reply_text(
            "¡Excelente! Ahora envíame el logo del evento como una foto."
        )
        return ESPERANDO_LOGO
    except ValueError:
        await update.message.reply_text(
            "Formato de fecha incorrecto. Por favor, envíala en formato YYYYMMDD HHMM."
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