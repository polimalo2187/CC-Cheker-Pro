import os
import string
import random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config.config import BOT_TOKEN, ADMIN_ID
from database.mongo import get_user, add_user, get_all_users, update_user
from payments.plan_purchase import buy_plan, confirm_plan_payment
from checker.checker import check_batch

# ==================================================
# Funciones de referidos
# ==================================================
def generate_ref_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def add_referral(new_user_id, ref_code):
    referrer = None
    users = get_all_users()
    for u in users:
        if u.get("ref_code") == ref_code:
            referrer = u
            break
    if not referrer or referrer["user_id"] == new_user_id:
        return

    new_user = get_user(new_user_id)
    update_user(new_user_id, {"referred_by": ref_code})

    plan = new_user.get("plan", "Free")
    if plan == "Free":
        credit = 1
    elif plan == "Basic":
        credit = 10
    elif plan == "Pro":
        credit = 25
    elif plan == "Ultra":
        credit = 50
    else:
        credit = 0

    referrer_credits = referrer.get("credits", 0) + credit
    update_user(referrer["user_id"], {"credits": referrer_credits})

# ==================================================
# Menú principal
# ==================================================
async def send_main_menu(chat_id, context: ContextTypes.DEFAULT_TYPE, user_id=None):
    keyboard = [
        [InlineKeyboardButton("💳 Verificar tarjetas", callback_data="menu_check")],
        [InlineKeyboardButton("💰 Comprar plan", callback_data="menu_buy")],
        [InlineKeyboardButton("📊 Mis créditos", callback_data="menu_credits")],
        [InlineKeyboardButton("❓ Soporte", callback_data="menu_support")],
        [InlineKeyboardButton("🔗 Referidos", callback_data="menu_referrals")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Panel Admin", callback_data="menu_admin")])
    await context.bot.send_message(
        chat_id,
        "Selecciona una opción:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==================================================
# /start
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user = get_user(user_id)
    if not user:
        code = generate_ref_code()
        add_user(user_id, ref_code=code)
        args = context.args
        if args:
            await add_referral(user_id, args[0])
    await send_main_menu(chat_id, context, user_id)

# ==================================================
# Manejo de botones
# ==================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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
        await query.edit_message_text(
            chat_id=chat_id,
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
            await context.bot.send_message(
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

    # -------------------------
    # Créditos
    # -------------------------
    if data == "menu_credits":
        user = get_user(user_id)
        plan = user.get("plan", "Free")
        credits = user.get("credits", 0)
        text = f"📊 Tu plan: {plan}\n"
        text += "♾ Créditos: Ilimitados" if plan == "Ultra" else f"🎟 Créditos disponibles: {credits}"
        await query.edit_message_text(chat_id=chat_id, text=text)
        return

    # -------------------------
    # Referidos
    # -------------------------
    if data == "menu_referrals":
        user = get_user(user_id)
        ref_code = user.get("ref_code", "N/A")
        msg = f"🔗 Tu código de referido: {ref_code}\n"
        msg += f"👥 Referidos válidos: {len(user.get('valid_referrals', []))}\n"
        msg += f"💰 Créditos obtenidos: {user.get('credits', 0)}"
        await query.edit_message_text(chat_id=chat_id, text=msg)
        return

    # -------------------------
    # Soporte
    # -------------------------
    if data == "menu_support":
        await query.edit_message_text(chat_id=chat_id, text="Soporte: contacta con el administrador.")
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
        await query.edit_message_text(chat_id=chat_id, text="Panel Admin:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # -------------------------
    # Admin -> Ver usuarios
    # -------------------------
    if data == "admin_users" and user_id == ADMIN_ID:
        users = get_all_users()
        msg = "👥 Usuarios registrados:\n\n"
        for u in users:
            msg += f"ID: {u['user_id']} | Plan: {u.get('plan','Free')} | Créditos: {u.get('credits',0)}\n"
        await query.edit_message_text(chat_id=chat_id, text=msg)
        return

    # -------------------------
    # Admin -> Reset créditos
    # -------------------------
    if data == "admin_reset" and user_id == ADMIN_ID:
        users = get_all_users()
        for u in users:
            if u.get("plan") != "Ultra":
                update_user(u["user_id"], {"credits": 0})
        await query.edit_message_text(chat_id=chat_id, text="✅ Créditos reseteados para todos los planes limitados.")
        return

    # -------------------------
    # Admin -> Estadísticas
    # -------------------------
    if data == "admin_stats" and user_id == ADMIN_ID:
        total_users_count = len(get_all_users())
        total_credits_count = sum(u.get("credits", 0) for u in get_all_users())
        text = f"📊 Estadísticas globales:\n\nUsuarios registrados: {total_users_count}\n"
        text += f"Créditos totales acumulados: {total_credits_count}"
        await query.edit_message_text(chat_id=chat_id, text=text)
        return

    # -------------------------
    # Volver al menú principal
    # -------------------------
    if data == "menu_main":
        await send_main_menu(chat_id, context, user_id)
        return

# ==================================================
# Recepción de tarjetas (texto o archivo)
# ==================================================
async def receive_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_cards"):
        return
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if update.message.document:
        file = await update.message.document.get_file()
        content = await file.download_as_bytearray()
        content = content.decode("utf-8")
        cards = [l.strip() for l in content.splitlines() if l.strip()]
    else:
        cards = [l.strip() for l in update.message.text.splitlines() if l.strip()]

    context.user_data["awaiting_cards"] = False
    result = check_batch(user_id, cards)
    if "error" in result:
        await context.bot.send_message(chat_id, f"❌ {result['error']}")
        return

    msg = (
        "✅ Resultado del lote:\n\n"
        f"💳 Total: {result['total']}\n"
        f"🟢 Life: {result['valid_life']}\n"
        f"🟡 CVV: {result['valid_cvv']}\n"
        f"🔴 Inválidas: {result['invalid']}"
    )
    await context.bot.send_message(chat_id, msg)
    await send_main_menu(chat_id, context, user_id)

# ==================================================
# Inicio
# ==================================================
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, receive_cards))

    print("✅ Bot iniciado correctamente")
    app.run_polling()
