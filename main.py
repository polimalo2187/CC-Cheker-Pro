# main.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from bot.bot import process_lote
from checker.provider import CheckerProvider, CheckerProviderError

# Tomar BOT_TOKEN y ADMIN_ID desde variables de entorno
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))  # convertir a int si viene como string

# ==================================================
# Menú principal
# ==================================================
async def send_main_menu(chat_id, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💳 Verificar tarjetas", callback_data="menu_check")]
    ]
    await context.bot.send_message(
        chat_id,
        "Selecciona una opción:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==================================================
# /start
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await send_main_menu(chat_id, context)

# ==================================================
# Manejo de botones
# ==================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id
    data = query.data

    # -------------------------
    # Checker
    # -------------------------
    if data == "menu_check":
        await query.edit_message_text(
            chat_id=chat_id,
            text=(
                "Envía tus tarjetas ahora.\n\n"
                "• Máximo 15 por lote\n"
                "• Formato: numero|mes|año|cvv\n"
                "• Puedes enviarlas como texto o archivo .txt"
            )
        )
        context.user_data["awaiting_cards"] = True
        return

# ==================================================
# Recepción de tarjetas (texto o archivo) con Apiverve
# ==================================================
async def receive_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_cards"):
        return
    chat_id = update.effective_chat.id

    if update.message.document:
        file = await update.message.document.get_file()
        content = await file.download_as_bytearray()
        content = content.decode("utf-8")
        cards = [l.strip() for l in content.splitlines() if l.strip()]
    else:
        cards = [l.strip() for l in update.message.text.splitlines() if l.strip()]

    context.user_data["awaiting_cards"] = False

    # ==========================
    # Procesar lote con bot.py
    # ==========================
    success, result = process_lote(cards)
    if not success:
        await context.bot.send_message(chat_id, f"❌ {result}")
        await send_main_menu(chat_id, context)
        return

    # Mostrar resumen
    detalles = result.get("detalles", [])
    msg = (
        "✅ Resultado del lote:\n\n"
        f"💳 Total: {result.get('total', len(cards))}\n"
        f"🟢 Life: {result.get('valid_life',0)}\n"
        f"🟡 CVV: {result.get('valid_cvv',0)}\n"
        f"🔴 Inválidas: {result.get('invalid',0)}"
    )

    await context.bot.send_message(chat_id, msg)
    await send_main_menu(chat_id, context)

# ==================================================
# Inicio
# ==================================================
if __name__ == "__main__":
    # Crear la aplicación
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Agregar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, receive_cards))

    print("✅ Bot iniciado correctamente")

    # Ejecutar el bot de manera asíncrona (v20+)
    import asyncio
    asyncio.run(app.run_polling())
