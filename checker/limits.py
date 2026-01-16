import time
from database.mongo import get_user, update_user

BATCH_LIMIT = 15
COOLDOWN = 600  # 10 minutos

def can_check_batch(user_id):
    user = get_user(user_id)
    last_check = user.get("last_check", 0)
    if time.time() - last_check < COOLDOWN:
        return False
    return True

def record_check(user_id, results):
    update_user(user_id, {"last_check": time.time()})
    # Aquí también puedes acumular estadísticas globales si quieres
