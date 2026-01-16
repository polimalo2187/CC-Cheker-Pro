import time
from limits import can_check_batch, record_check
from utils import validate_card

BATCH_LIMIT = 15  # máximo de tarjetas por lote
COOLDOWN = 600    # 10 minutos en segundos

def check_batch(cards_list):
    """
    Procesa un lote de tarjetas.
    cards_list = lista de strings de tarjetas (numero|mes|año|cvv)
    """

    # Limitar el lote
    if len(cards_list) > BATCH_LIMIT:
        return {"error": f"Máximo {BATCH_LIMIT} tarjetas por lote."}

    # Revisar cooldown
    if not can_check_batch():
        return {"error": f"Debes esperar antes de chequear otro lote (10 min)."}

    results = {"total": len(cards_list), "valid_cvv": 0, "valid_life": 0, "invalid": 0}

    for card in cards_list:
        status = validate_card(card)  # función que devuelve "CVV", "Life" o "Invalid"
        if status == "CVV":
            results["valid_cvv"] += 1
        elif status == "Life":
            results["valid_life"] += 1
        else:
            results["invalid"] += 1

    # Guardar registro del lote
    record_check(results)

    return results
