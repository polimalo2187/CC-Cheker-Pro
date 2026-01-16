# bot/bot.py
import os
import time
from checker.provider import CheckerProvider, CheckerProviderError

# ================================
# Configuración
# ================================
MAX_LOTE = 15          # máximo de tarjetas por lote
COOLDOWN = 0           # ahora tu eres ilimitado
_last_check_time = 0   # timestamp del último lote procesado

def process_lote(tarjetas: list):
    """
    Procesa un lote de tarjetas usando Apiverve.
    tarjetas -> lista de strings "numero|mes|año|cvc"
    Devuelve: (True, resultados) o (False, mensaje_error)
    """
    global _last_check_time

    now = time.time()
    if now - _last_check_time < COOLDOWN:
        wait_time = int(COOLDOWN - (now - _last_check_time))
        return False, f"Debes esperar {wait_time} segundos antes de procesar otro lote"

    if len(tarjetas) > MAX_LOTE:
        return False, f"Máximo {MAX_LOTE} tarjetas por lote"

    # Inicializar provider Apiverve
    try:
        provider = CheckerProvider()
    except CheckerProviderError as e:
        return False, f"Error inicializando Apiverve: {str(e)}"

    resultados = []
    valid_count = 0
    invalid_count = 0

    for line in tarjetas[:MAX_LOTE]:
        try:
            number, month, year, cvc = line.split("|")
        except ValueError:
            resultados.append({"card": line, "status": "FORMATO_INVALIDO"})
            invalid_count += 1
            continue

        try:
            status = provider.check_card(number, month, year, cvc)
        except Exception as e:
            resultados.append({"card": line, "status": f"ERROR: {str(e)}"})
            invalid_count += 1
            continue

        if status in ("LIVE", "CVV"):
            valid_count += 1
        else:
            invalid_count += 1

        resultados.append({"card": line, "status": status})

    # Actualizar timestamp del último lote
    _last_check_time = now

    summary = {
        "total": len(tarjetas),
        "valid_life": sum(1 for r in resultados if r["status"] == "LIVE"),
        "valid_cvv": sum(1 for r in resultados if r["status"] == "CVV"),
        "invalid": invalid_count,
        "detalles": resultados
    }

    return True, summary
