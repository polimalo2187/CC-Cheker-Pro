import time
import json
from bot.bot import send_message, process_lote, check_limits
from plans.plans import activate_plan, check_cycle_reset
from database.mongo import add_user, get_user, reset_daily_limits
from config.config import BOT_TOKEN, ADMIN_ID
import requests

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# -------------------------------
# Función para obtener actualizaciones
# -------------------------------
def get_updates(offset=None):
    url = BASE_URL + "getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"[ERROR GET_UPDATES] {e}")
        return None

# -------------------------------
# Función principal del bot
# -------------------------------
def main():
    print("Bot iniciado...")
    offset = None

    while True:
        updates = get_updates(offset)
        if updates and updates.get("ok"):
            for update in updates["result"]:
                offset = update["update_id"] + 1

                # Manejo de mensajes
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    userid = update["message"]["from"]["id"]
                    text = update["message"].get("text", "")

                    # Registro automático
                    add_user(userid)

                    # Reseteo de ciclo si aplica
                    check_cycle_reset(userid)

                    # Comandos básicos
                    if text == "/start":
                        send_message(chat_id, f"Hola! Bienvenido al Checker Bot. Tu plan actual es: {get_user(userid)['plan']}")
                        continue

                    if text.startswith("/plan"):
                        parts = text.split()
                        if len(parts) == 2:
                            plan_name = parts[1]
                            success, msg = activate_plan(userid, plan_name)
                            send_message(chat_id, msg)
                        else:
                            send_message(chat_id, "Uso: /plan [NombrePlan]")
                        continue

                    if text.startswith("/check"):
                        # Ejemplo: /check tarjeta1 tarjeta2 tarjeta3
                        tarjetas = text.split()[1:]
                        if not tarjetas:
                            send_message(chat_id, "Debes enviar al menos una tarjeta después de /check")
                            continue

                        # Verificar límites
                        can_check, msg = check_limits(userid)
                        if not can_check:
                            send_message(chat_id, msg)
                            continue

                        # Procesar lote
                        success, resultados = process_lote(userid, tarjetas)
                        if not success:
                            send_message(chat_id, resultados)
                        else:
                            msg_result = "\n".join([f"{r['tarjeta']}: {r['resultado']}" for r in resultados])
                            send_message(chat_id, f"Resultados del lote:\n{msg_result}")

        time.sleep(1)

if __name__ == "__main__":
    reset_daily_limits()  # Reinicia contadores diarios si aplica
    main()
