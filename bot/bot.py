import requests
from config.config import BOT_TOKEN, TIMEZONE, MAX_LOTE, ANTI_SPAM_TIMER
from database.mongo import get_user, increment_valid, can_process_lote, get_plan_limits, is_admin
from datetime import datetime

# -------------------------------
# Funciones básicas del bot
# -------------------------------

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

def bot_request(method, data=None):
    """Realiza una petición a la API de Telegram"""
    url = BASE_URL + method
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"[ERROR BOT REQUEST] {e}")
        return None

def send_message(chat_id, text, reply_markup=None):
    """Envía un mensaje de texto"""
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    return bot_request("sendMessage", data)

def edit_message(chat_id, message_id, text, reply_markup=None):
    """Edita un mensaje existente"""
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    return bot_request("editMessageText", data)

# -------------------------------
# Funciones para checker
# -------------------------------

def process_lote(userid, tarjetas):
    """
    Procesa un lote de tarjetas:
    - Verifica límite por lote (MAX_LOTE)
    - Verifica espera de 10 min entre lotes
    - Incrementa válidas LIVE/CVV
    """
    user = get_user(userid)
    if not user:
        return False, "Usuario no registrado"

    # Verifica si puede procesar lote
    can_process, wait_time = can_process_lote(userid, MAX_LOTE, ANTI_SPAM_TIMER)
    if not can_process:
        return False, f"Debes esperar {int(wait_time)} segundos antes de enviar otro lote."

    # Limitar tamaño de lote
    lote = tarjetas[:MAX_LOTE]

    # Aquí va la lógica de verificación de tarjetas (LIVE/CVV)
    resultados = []
    valid_count = 0
    for tarjeta in lote:
        # Simulación de verificación (pendiente de integración real con SK Key)
        # Por ahora, aleatorio como ejemplo
        # LIVE y CVV cuentan como válidas
        if tarjeta.endswith("0"):  # ejemplo: tarjetas terminadas en 0 = LIVE
            resultado = "LIVE"
            valid_count += 1
        elif tarjeta.endswith("1"):  # ejemplo: tarjetas terminadas en 1 = CVV
            resultado = "CVV"
            valid_count += 1
        else:
            resultado = "DEAD"
        resultados.append({"tarjeta": tarjeta, "resultado": resultado})

    # Incrementar válidas en Mongo
    if not is_admin(userid) and user["plan"] != "Ultra":
        increment_valid(userid, valid_count)

    return True, resultados

def check_limits(userid):
    """Verifica si el usuario alcanzó el límite de válidas de su plan"""
    user = get_user(userid)
    if not user:
        return False, "Usuario no registrado"

    if is_admin(userid) or user["plan"] == "Ultra":
        return True, None  # ilimitado

    valid_limit = get_plan_limits(userid)
    if user.get("valid_today", 0) >= valid_limit:
        return False, "Has alcanzado el límite de tarjetas válidas de tu plan. Compra créditos o espera el próximo ciclo."
    return True, None
