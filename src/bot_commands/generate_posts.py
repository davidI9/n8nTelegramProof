from datetime import datetime
from pathlib import Path

from telegram import Update
from repositories.template_repository import TemplateRepository
from repositories.generate_assets_repository import GenerateAssetsRepository
from repositories.create_project_repository import CreateProjectRepository
from handlers.generate_template_handler import GenerateTemplateHandler
from handlers.generate_posts_handler import GeneratePostsHandler
from dtos.generate_template_dto import GenerateTemplateDTO
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
        script_path=str(Path(__file__).resolve().parents[1] / "shared" / "create-project.sh"),
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
    event_date = update.message.text
    
    try:
        datetime.strptime(event_date, "%Y%m%d %H%M")
    except ValueError:
        await update.message.reply_text(
            "Formato de fecha incorrecto. Por favor, envíala en formato YYYYMMDD HHMM."
        )
        return ESPERANDO_DATE

    dto.event_date = event_date
    repository = CreateProjectRepository()
    handler = GenerateTemplateHandler(repository)
    generated_paths = handler.handle(dto)

    if not generated_paths:
        await update.message.reply_text(
            "No se pudo generar la plantilla base. Revisa logs y vuelve a intentarlo."
        )
        return ConversationHandler.END

    context.user_data['template_path'] = generated_paths.get('template_path')
    context.user_data['generate_script_path'] = generated_paths.get('generate_script_path')
    
    await update.message.reply_text(
        "¡Excelente! Ahora envíame el logo del evento como una foto."
    )
    return ESPERANDO_LOGO

async def recibir_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    template_repository = TemplateRepository()
    assets_repository = GenerateAssetsRepository()
    handler = GeneratePostsHandler(template_repository, assets_repository)
    
    foto_id = update.message.photo[-1].file_id
    file = await context.bot.get_file(foto_id)
    
    file_path = str(Path(__file__).resolve().parents[1] / "shared" / "temporal_logo.jpg")
    template_path = context.user_data['template_path']
    generate_script_path = context.user_data['generate_script_path']
    await file.download_to_drive(file_path)

    if not template_path or not Path(template_path).is_file():
        await update.message.reply_text(
            "No se encontró la plantilla generada para sobrescribir el SVG."
        )
        return ConversationHandler.END

    if not generate_script_path or not Path(generate_script_path).is_file():
        await update.message.reply_text(
            "No se encontró el script generate.sh en la carpeta de la actividad."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"¡Logo recibido y descargado! ✅\n\n(Procesando la plantilla...)"
    )
    
    ok = handler.handle(file_path, template_path, generate_script_path)

    if ok:
        await update.message.reply_text("¡Listo! Se actualizó el SVG y se ejecutó generate.sh ✅")
    else:
        await update.message.reply_text(
            "El SVG se actualizó, pero falló la ejecución de generate.sh. Revisa logs."
        )
    
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operación cancelada. ¡Avísame cuando me necesites!")
    return ConversationHandler.END

post_handler = ConversationHandler(
    entry_points=[CommandHandler("crear_cartel", crear_cartel)],
    states={
        ESPERANDO_LOGO: [MessageHandler(filters.PHOTO, recibir_logo)],
        ESPERANDO_FIRST_LINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_first_line)],
        ESPERANDO_SECOND_LINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_second_line)],
        ESPERANDO_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)]
    },
    fallbacks=[CommandHandler("cancelar", cancelar)]
)