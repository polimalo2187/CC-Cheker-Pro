from database.mongo import get_user, update_user
from plans.plans import activate_plan
from payments.usdt_bep20 import check_payment, credit_user
from bot.bot import send_message
from config.config import PAYMENT_WALLET

# -------------------------------
# Flujo de compra de plan
# -------------------------------

PLAN_COSTS = {
    "Free": 0,
    "Basic": 10,   # USDT
    "Pro": 25,     # USDT
    "Ultra": 50    # USDT
}

CREDITS_PER_PLAN = {
    "Free": 0,
    "Basic": 10,      # créditos internos
    "Pro": 30,        # créditos internos
    "Ultra": float("inf")  # Ultra = ilimitado
}

def buy_plan(userid, chat_id, plan_name):
    """
    Flujo completo de compra de plan
    """

    user = get_user(userid)
    if not user:
        send_message(chat_id, "❌ Usuario no registrado.")
        return

    if plan_name not in PLAN_COSTS:
        send_message(chat_id, f"❌ Plan '{plan_name}' no existe.")
        return

    # Mostrar wallet y monto
    usdt_amount = PLAN_COSTS[plan_name]
    if usdt_amount == 0:
        # Plan Free
        success, msg = activate_plan(userid, plan_name)
        send_message(chat_id, msg)
        return

    msg = (
        f"💰 Para comprar el plan <b>{plan_name}</b> envía {usdt_amount} USDT BEP20 a la siguiente wallet:\n\n"
        f"<code>{PAYMENT_WALLET}</code>\n\n"
        "Después de enviar, escribe /confirmplan para verificar el pago."
    )
    send_message(chat_id, msg)

def confirm_plan_payment(userid, chat_id, plan_name):
    """
    Confirma el pago USDT BEP20 y activa el plan
    """
    if plan_name not in PLAN_COSTS:
        send_message(chat_id, f"❌ Plan '{plan_name}' no existe.")
        return

    usdt_amount = PLAN_COSTS[plan_name]
    credit_value = CREDITS_PER_PLAN[plan_name]

    # Verificar pago en blockchain
    if check_payment(PAYMENT_WALLET, usdt_amount):
        # Ultra ilimitado → no contamos créditos
        if credit_value != float("inf"):
            success, msg = credit_user(userid, usdt_amount, credit_value)
            if not success:
                send_message(chat_id, f"❌ Error al acreditar créditos: {msg}")
                return
        else:
            msg = f"✅ Plan Ultra activado: uso ilimitado"

        # Activar plan
        success, msg2 = activate_plan(userid, plan_name)
        send_message(chat_id, f"{msg}\n{msg2}")
    else:
        send_message(chat_id, f"❌ No se ha recibido {usdt_amount} USDT todavía. Espera unos minutos y prueba de nuevo.")
