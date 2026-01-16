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
from checker.checker import check_batch
from checker.provider import CheckerProvider, CheckerProviderError

# Variables de entorno
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APIVERBE = os.environ.get("APIverbe")

# ==================================================
# Menú principal
# ==================================================
async def send_main_menu(chat_id, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        [InlineKeyboardButton("💳 Verificar tarjetas", callback_data="menu_check")]
    ]
    await context.bot.send_message(
        chat_id,
        "Selecciona una opción:",
        reply_markup=InlineKeyboardMarkup(teclado)
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

# ==================================================
# Recepción de tarjetas
# ==================================================
async def receive_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_cards"):
        return
    chat_id = update.effective_chat.id

    if update.message.document:
        archivo = await update.message.document.get_file()
        contenido = await archivo.download_as_bytearray()
        contenido = contenido.decode("utf-8")
        tarjetas = [l.strip() for l in contenido.splitlines() if l.strip()]
    else:
        tarjetas = [l.strip() for l in update.message.text.splitlines() if l.strip()]

    context.user_data["awaiting_cards"] = False

    # ==========================
    # Procesar con proveedor APIverbe
    # ==========================
    try:
        proveedor = CheckerProvider(APIVERBE)
    except CheckerProviderError as e:
        await context.bot.send_message(chat_id, f"❌ Error: {str(e)}")
        return

    resultados = []
    valid_life = 0
    valid_cvv = 0
    invalid = 0

    for linea in tarjetas[:15]:
        try:
            numero, mes, año, cvv = linea.split("|")
        except ValueError:
            resultados.append({"card": linea, "status": "FORMATO_INVALIDO"})
            invalid += 1
            continue
        try:
            status = proveedor.check_card(numero, mes, año, cvv)
        except Exception as e:
            resultados.append({"card": linea, "status": f"ERROR: {str(e)}"})
            invalid += 1
            continue

        if status == "LIVE":
            valid_life += 1
        elif status == "CVV":
            valid_cvv += 1
        else:
            invalid += 1

        resultados.append({"card": linea, "status": status})

    mensaje = (
        "✅ Resultado del lote:\n\n"
        f"💳 Total: {len(tarjetas)}\n"
        f"🟢 Life: {valid_life}\n"
        f"🟡 CVV: {valid_cvv}\n"
        f"🔴 Inválidas: {invalid}"
    )
    await context.bot.send_message(chat_id, mensaje)
    await send_main_menu(chat_id, context)

# ==================================================
# Inicio del bot
# ==================================================
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, receive_cards))

    print("✅ Bot iniciado correctamente")
    app.run_polling()
