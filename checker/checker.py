# checker/checker.py

from checker.provider import CheckerProvider

BATCH_LIMIT = 15  # máximo por lote

def check_batch(tarjetas):
    """
    Procesa un lote de tarjetas (lista de strings: numero|mes|año|cvv)
    """
    if len(tarjetas) > BATCH_LIMIT:
        return {"error": f"Máximo {BATCH_LIMIT} tarjetas por lote."}

    proveedor = CheckerProvider()

    resultados = {"total": len(tarjetas), "valid_cvv": 0, "valid_life": 0, "invalid": 0}

    for linea in tarjetas[:BATCH_LIMIT]:
        try:
            numero, mes, año, cvv = linea.split("|")
        except ValueError:
            resultados["invalid"] += 1
            continue

        try:
            status = proveedor.check_card(numero, mes, año, cvv)
        except:
            status = "ERROR"
            resultados["invalid"] += 1
            continue

        if status == "LIVE":
            resultados["valid_life"] += 1
        elif status == "CVV":
            resultados["valid_cvv"] += 1
        else:
            resultados["invalid"] += 1

    return resultados
