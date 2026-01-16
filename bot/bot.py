from checker.provider import CheckerProvider, CheckerProviderError
from database.mongo import (
    get_user,
    increment_valid,
    can_process_lote,
    is_admin,
)
from config.config import MAX_LOTE, ANTI_SPAM_TIMER


def process_lote(userid: int, tarjetas: list):
    """
    Procesa un lote REAL de tarjetas usando Apiverve.
    """
    user = get_user(userid)
    if not user:
        return False, "Usuario no registrado"

    # Control de tiempo entre lotes
    can_process, wait_time = can_process_lote(
        userid, MAX_LOTE, ANTI_SPAM_TIMER
    )
    if not can_process:
        return False, f"Debes esperar {int(wait_time)} segundos"

    # Inicializar provider REAL (Apiverve)
    try:
        provider = CheckerProvider()
    except CheckerProviderError as e:
        return False, str(e)

    resultados = []
    valid_count = 0

    for line in tarjetas[:MAX_LOTE]:
        try:
            number, month, year, cvc = line.split("|")
        except ValueError:
            resultados.append({
                "card": line,
                "status": "FORMATO_INVALIDO"
            })
            continue

        try:
            # check_card ahora apunta a Apiverve
            status = provider.check_card(number, month, year, cvc)
        except Exception as e:
            resultados.append({
                "card": line,
                "status": f"ERROR: {str(e)}"
            })
            continue

        if status in ("LIVE", "CVV"):
            valid_count += 1

        resultados.append({
            "card": line,
            "status": status
        })

    # Contar SOLO válidas (excepto admin / ultra)
    if not is_admin(userid) and user["plan"] != "Ultra":
        increment_valid(userid, valid_count)

    return True, resultados
