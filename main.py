import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from config.config import BOT_TOKEN
from payments.plan_purchase import buy_plan, confirm_plan_payment
from database.mongo import get_user
from admin.admin_panel import handle_admin_command

# -------------------------------
# Inicializar bot Telegram
# -------------------------------
updater = Updater(BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# -------------------------------
# Comando start
# -------------------------------
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user = get_user(user_id)

    if not user:
        from database.mongo import add_user
        add_user(user_id)

    context.bot.send_message(chat_id, f"Hola {update.effective_user.first_name}, bienvenido al bot!")

dispatcher.add_handler(CommandHandler("start", start))

# -------------------------------
# Comando buyplan
# -------------------------------
def buyplan(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if len(context.args) != 1:
        context.bot.send_message(chat_id, "Uso: /buyplan [Plan]")
        return

    plan_name = context.args[0]
    buy_plan(user_id, chat_id, plan_name)

dispatcher.add_handler(CommandHandler("buyplan", buyplan))

# -------------------------------
# Comando confirmplan
# -------------------------------
def confirmplan(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if len(context.args) != 1:
        context.bot.send_message(chat_id, "Uso: /confirmplan [Plan]")
        return

    plan_name = context.args[0]
    confirm_plan_payment(user_id, chat_id, plan_name)

dispatcher.add_handler(CommandHandler("confirmplan", confirmplan))

# -------------------------------
# Comandos admin
# -------------------------------
def admin_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text

    handle_admin_command(user_id, chat_id, text)

dispatcher.add_handler(MessageHandler(Filters.text & Filters.user(user_id=None), admin_command))

# -------------------------------
# Iniciar bot
# -------------------------------
if __name__ == "__main__":
    print("Bot iniciado...")
    updater.start_polling()
    updater.idle()
