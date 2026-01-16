import time
from database.mongo import get_user, update_user
from limits import can_check_batch, record_check
from utils import validate_card

BATCH_LIMIT = 15  # tarjetas por lote
COOLDOWN = 600    # 10 minutos en segundos

def check_batch(user_id, cards_list):
    """
    Procesa un lote de tarjetas para un usuario.
    cards_list = lista de strings de tarjetas
    """

    # Limitar el lote
    if len(cards_list) > BATCH_LIMIT:
        return {"error": f"Máximo {BATCH_LIMIT} tarjetas por lote."}

    # Revisar cooldown
    if not can_check_batch(user_id):
        return {"error": f"Debes esperar antes de chequear otro lote."}

    results = {"total": len(cards_list), "valid_cvv": 0, "valid_life": 0, "invalid": 0}
    user = get_user(user_id)
    plan = user.get("plan", "Free")
    credits = user.get("credits", 0)

    for card in cards_list:
        status = validate_card(card)  # función que devuelve "CVV", "Life" o "Invalid"
        if status == "CVV":
            results["valid_cvv"] += 1
        elif status == "Life":
            results["valid_life"] += 1
        else:
            results["invalid"] += 1

        # Descontar crédito si no es Ultra ilimitado
        if plan != "Ultra" and status in ["CVV", "Life"]:
            if credits > 0:
                credits -= 1
            else:
                break  # usuario sin créditos

    # Guardar créditos y registro del lote
    update_user(user_id, {"credits": credits})
    record_check(user_id, results)

    return results
