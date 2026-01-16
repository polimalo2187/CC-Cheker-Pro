import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)

from config.config import BOT_TOKEN, ADMIN_ID
from database.mongo import get_user, add_user, get_all_users, update_user
from payments.plan_purchase import buy_plan, confirm_plan_payment
from checker.checker import check_batch

# ==================================================
# Inicialización del bot
# ==================================================
updater = Updater(BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# ==================================================
# Menú principal
# ==================================================
def send_main_menu(chat_id, context: CallbackContext, user_id=None):
    keyboard = [
        [InlineKeyboardButton("💳 Verificar tarjetas", callback_data="menu_check")],
        [InlineKeyboardButton("💰 Comprar plan", callback_data="menu_buy")],
        [InlineKeyboardButton("📊 Mis créditos", callback_data="menu_credits")],
        [InlineKeyboardButton("❓ Soporte", callback_data="menu_support")]
    ]
    # Agregar botón admin solo si es el dueño
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Panel Admin", callback_data="menu_admin")])

    context.bot.send_message(
        chat_id,
        "Selecciona una opción:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==================================================
# /start
# ==================================================
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    user = get_user(user_id)
    if not user:
        add_user(user_id)

    send_main_menu(chat_id, context, user_id)

# ==================================================
# Manejo de botones
# ==================================================
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    chat_id = query.message.chat.id
    data = query.data

    # -------------------------
    # Comprar plan
    # -------------------------
    if data == "menu_buy":
        keyboard = [
            [InlineKeyboardButton("Free", callback_data="buy_Free")],
            [InlineKeyboardButton("Basic", callback_data="buy_Basic")],
            [InlineKeyboardButton("Pro", callback_data="buy_Pro")],
            [InlineKeyboardButton("Ultra (Ilimitado)", callback_data="buy_Ultra")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="menu_main")]
        ]
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text="Selecciona el plan:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("buy_"):
        plan = data.split("_")[1]
        buy_plan(user_id, chat_id, plan)
        if plan != "Free":
            keyboard = [
                [InlineKeyboardButton("✅ Confirmar pago", callback_data=f"confirm_{plan}")],
                [InlineKeyboardButton("⬅️ Volver", callback_data="menu_main")]
            ]
            context.bot.send_message(
                chat_id,
                "Cuando hayas enviado el pago, confirma:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return

    if data.startswith("confirm_"):
        plan = data.split("_")[1]
        confirm_plan_payment(user_id, chat_id, plan)
        return

    # -------------------------
    # Checker
    # -------------------------
    if data == "menu_check":
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=(
                "Envía tus tarjetas ahora.\n\n"
                "• Máximo 15 por lote\n"
                "• Formato: numero|mes|año|cvv\n"
                "• Puedes enviarlas como texto o archivo .txt"
            )
        )
        context.user_data["awaiting_cards"] = True
        return

    # -------------------------
    # Créditos
    # -------------------------
    if data == "menu_credits":
        user = get_user(user_id)
        plan = user.get("plan", "Free")
        credits = user.get("credits", 0)

        text = f"📊 Tu plan: {plan}\n"
        text += "♾ Créditos: Ilimitados" if plan == "Ultra" else f"🎟 Créditos disponibles: {credits}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text=text
        )
        return

    # -------------------------
    # Soporte
    # -------------------------
    if data == "menu_support":
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text="Soporte: contacta con el administrador."
        )
        return

    # -------------------------
    # Panel Admin
    # -------------------------
    if data == "menu_admin" and user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("👥 Ver usuarios", callback_data="admin_users")],
            [InlineKeyboardButton("🔄 Reset créditos", callback_data="admin_reset")],
            [InlineKeyboardButton("📊 Estadísticas globales", callback_data="admin_stats")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="menu_main")]
        ]
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=query.message.message_id,
            text="Panel Admin:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # -------------------------
    # Admin -> Ver usuarios
    # -------------------------
    if data == "admin_users" and user_id == ADMIN_ID:
        users = get_all_users()
        msg = "👥 Usuarios registrados:\n\n"
        for u in users:
            msg += f"ID: {u['user_id']} | Plan: {u.get('plan','Free')} | Créditos: {u.get('credits',0)}\n"
        context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=msg)
        return

    # -------------------------
    # Admin -> Reset créditos
    # -------------------------
    if data == "admin_reset" and user_id == ADMIN_ID:
        users = get_all_users()
        for u in users:
            if u.get("plan") != "Ultra":
                update_user(u["user_id"], {"credits": 0})
        context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text="✅ Créditos reseteados para todos los planes limitados.")
        return

    # -------------------------
    # Admin -> Estadísticas
    # -------------------------
    if data == "admin_stats" and user_id == ADMIN_ID:
        total_users = len(get_all_users())
        text = f"📊 Estadísticas globales:\n\nUsuarios registrados: {total_users}\n"
        context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=text)
        return

    # -------------------------
    # Volver al menú principal
    # -------------------------
    if data == "menu_main":
        send_main_menu(chat_id, context, user_id)
        return

# ==================================================
# Recepción de tarjetas (texto o archivo)
# ==================================================
def receive_cards(update: Update, context: CallbackContext):
    if not context.user_data.get("awaiting_cards"):
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Obtener tarjetas
    if update.message.document:
        file = update.message.document.get_file()
        content = file.download_as_bytearray().decode("utf-8")
        cards = [l.strip() for l in content.splitlines() if l.strip()]
    else:
        cards = [l.strip() for l in update.message.text.splitlines() if l.strip()]

    context.user_data["awaiting_cards"] = False

    result = check_batch(user_id, cards)

    if "error" in result:
        context.bot.send_message(chat_id, f"❌ {result['error']}")
        return

    msg = (
        "✅ Resultado del lote:\n\n"
        f"💳 Total: {result['total']}\n"
        f"🟢 Life: {result['valid_life']}\n"
        f"🟡 CVV: {result['valid_cvv']}\n"
        f"🔴 Inválidas: {result['invalid']}"
    )

    context.bot.send_message(chat_id, msg)
    send_main_menu(chat_id, context, user_id)

# ==================================================
# Handlers
# ==================================================
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(button_handler))
dispatcher.add_handler(MessageHandler(Filters.text | Filters.document, receive_cards))

# ==================================================
# Inicio
# ==================================================
if __name__ == "__main__":
    print("✅ Bot iniciado correctamente")
    updater.start_polling()
    updater.idle()
