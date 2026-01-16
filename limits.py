import time
from database.mongo import get_user, update_user

BATCH_LIMIT = 15
COOLDOWN = 600  # 10 minutos en segundos

def can_check_batch(user_id):
    """
    Verifica si el usuario puede chequear un nuevo lote según el cooldown.
    Retorna True si puede chequear, False si aún debe esperar.
    """
    user = get_user(user_id)
    last_check = user.get("last_check", 0)
    if time.time() - last_check < COOLDOWN:
        return False
    return True

def record_check(user_id, results):
    """
    Actualiza el último timestamp de chequeo del usuario y opcionalmente estadísticas globales.
    results = dict con keys: total, valid_cvv, valid_life, invalid
    """
    update_user(user_id, {"last_check": time.time()})
    # Si quieres acumular estadísticas globales, aquí se puede agregar:
    # update_global_stats(results)
