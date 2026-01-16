import time

BATCH_LIMIT = 15      # máximo de tarjetas por lote
COOLDOWN = 600        # 10 minutos en segundos
_last_check_time = 0  # registro interno del último lote

def _can_check_batch():
    """Verifica si pasó el cooldown desde el último lote"""
    global _last_check_time
    now = time.time()
    if now - _last_check_time >= COOLDOWN:
        return True
    return False

def _record_check():
    """Actualiza el tiempo del último chequeo"""
    global _last_check_time
    _last_check_time = time.time()

def validate_card(card):
    """
    Función de ejemplo de validación de tarjeta.
    Debe devolver: "CVV", "Life" o "Invalid".
    """
    # Aquí va tu lógica de validación real
    # Por ahora ponemos dummy:
    if "0" in card:
        return "Invalid"
    elif "1" in card:
        return "CVV"
    else:
        return "Life"

def check_batch(cards_list):
    """
    Procesa un lote de tarjetas.
    cards_list = lista de strings de tarjetas (numero|mes|año|cvv)
    """
    if len(cards_list) > BATCH_LIMIT:
        return {"error": f"Máximo {BATCH_LIMIT} tarjetas por lote."}

    if not _can_check_batch():
        return {"error": f"Debes esperar antes de chequear otro lote (10 min)."}

    results = {"total": len(cards_list), "valid_cvv": 0, "valid_life": 0, "invalid": 0}

    for card in cards_list:
        status = validate_card(card)
        if status == "CVV":
            results["valid_cvv"] += 1
        elif status == "Life":
            results["valid_life"] += 1
        else:
            results["invalid"] += 1

    _record_check()
    return results
