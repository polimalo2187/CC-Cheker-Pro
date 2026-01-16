import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackContext, CallbackQueryHandler, CommandHandler
from config.config import BOT_TOKEN, ADMIN_ID
from database.mongo import get_user, add_user
from payments.plan_purchase import buy_plan, confirm_plan_payment
from admin.admin_panel import handle_admin_command

# -------------------------------
# Inicializar bot
# -------------------------------
updater = Updater(BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# -------------------------------
# Comando /start
# -------------------------------
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user = get_user(user_id)
    if not user:
        add_user(user_id)

    keyboard = [
        [InlineKeyboardButton("Comprar plan 💰", callback_data="menu_buy")],
        [InlineKeyboardButton("Ver créditos 📊", callback_data="menu_credits")],
        [InlineKeyboardButton("Soporte/FAQ ❓", callback_data="menu_support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id, "Bienvenido al bot. Selecciona una opción:", reply_markup=reply_markup)

# -------------------------------
# Callback para botones
# -------------------------------
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    data = query.data

    # ---------------------------
    # Menu principal usuario
    # ---------------------------
    if data == "menu_buy":
        keyboard = [
            [InlineKeyboardButton("Free", callback_data="buy_Free")],
            [InlineKeyboardButton("Basic", callback_data="buy_Basic")],
            [InlineKeyboardButton("Pro", callback_data="buy_Pro")],
            [InlineKeyboardButton("Ultra", callback_data="buy_Ultra")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="menu_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=query.message.message_id,
                                      text="Selecciona el plan que deseas comprar:",
                                      reply_markup=reply_markup)
        return

    if data.startswith("buy_"):
        plan_name = data.split("_")[1]
        buy_plan(user_id, chat_id, plan_name)
        # Mostrar botón Confirmar pago solo si no es Free
        if plan_name != "Free":
            keyboard = [[InlineKeyboardButton("✅ Confirmar pago", callback_data=f"confirm_{plan_name}")],
                        [InlineKeyboardButton("⬅️ Volver", callback_data="menu_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id, f"Después de enviar el pago, confirma:", reply_markup=reply_markup)
        return

    if data.startswith("confirm_"):
        plan_name = data.split("_")[1]
        confirm_plan_payment(user_id, chat_id, plan_name)
        return

    if data == "menu_credits":
        user = get_user(user_id)
        credits = user.get("credits", 0)
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=query.message.message_id,
                                      text=f"Tienes {credits} créditos disponibles hoy.")
        return

    if data == "menu_support":
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=query.message.message_id,
                                      text="Soporte: contacta con el admin @TuUsuario")
        return

    if data == "menu_main":
        start(update, context)
        return

    # ---------------------------
    # Admin botones
    # ---------------------------
    if user_id == ADMIN_ID:
        handle_admin_command(user_id, chat_id, data)

# -------------------------------
# Agregar handlers
# -------------------------------
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(button_handler))

# -------------------------------
# Iniciar bot
# -------------------------------
if __name__ == "__main__":
    print("Bot interactivo iniciado...")
    updater.start_polling()
    updater.idle()
