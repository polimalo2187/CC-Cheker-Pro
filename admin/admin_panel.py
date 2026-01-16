from bot.bot import send_message, edit_message
from database.mongo import get_user, update_user, reset_daily_limits
from plans.plans import activate_plan, add_credits
from config.config import ADMIN_ID

# -------------------------------
# Panel Admin
# -------------------------------

def handle_admin_command(userid, chat_id, text):
    """
    Maneja comandos de administrador
    """

    # Solo el admin puede usar estos comandos
    if userid != ADMIN_ID:
        send_message(chat_id, "❌ No tienes permisos de administrador.")
        return

    # ---------------------------
    # /users -> Lista de usuarios
    # ---------------------------
    if text.startswith("/users"):
        users = []
        # Extraemos todos los usuarios de Mongo
        from database.mongo import db
        for u in db.users.find():
            users.append(f"{u['userid']} | Plan: {u['plan']} | Válidas hoy: {u.get('valid_today',0)} | Ultra: {u.get('plan','')=='Ultra'}")
        if users:
            send_message(chat_id, "<b>Usuarios registrados:</b>\n" + "\n".join(users))
        else:
            send_message(chat_id, "No hay usuarios registrados.")
        return

    # ---------------------------
    # /plan [userid] [Plan] -> Cambiar plan de usuario
    # ---------------------------
    if text.startswith("/plan "):
        try:
            parts = text.split()
            target_id = int(parts[1])
            plan_name = parts[2]
        except (IndexError, ValueError):
            send_message(chat_id, "Uso: /plan [userid] [Plan]")
            return

        success, msg = activate_plan(target_id, plan_name)
        send_message(chat_id, msg)
        return

    # ---------------------------
    # /credits [userid] [cantidad] -> Agregar créditos
    # ---------------------------
    if text.startswith("/credits "):
        try:
            parts = text.split()
            target_id = int(parts[1])
            amount = int(parts[2])
        except (IndexError, ValueError):
            send_message(chat_id, "Uso: /credits [userid] [cantidad]")
            return

        success, msg = add_credits(target_id, amount)
        send_message(chat_id, msg)
        return

    # ---------------------------
    # /reset -> Reiniciar contadores diarios
    # ---------------------------
    if text.startswith("/reset"):
        reset_daily_limits()
        send_message(chat_id, "✅ Contadores diarios reiniciados correctamente.")
        return

    # ---------------------------
    # Comando desconocido
    # ---------------------------
    send_message(chat_id, "Comando admin no reconocido.")
