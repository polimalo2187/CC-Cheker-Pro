from pymongo import MongoClient
from config.config import MONGO_URI, MONGO_DB_NAME
from datetime import datetime, timedelta

# -------------------------------
# Conexión a MongoDB
# -------------------------------
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# -------------------------------
# Funciones de usuario
# -------------------------------

def get_user(userid):
    """Obtiene el usuario por su ID"""
    return db.users.find_one({"userid": userid})

def add_user(userid):
    """Agrega un nuevo usuario si no existe"""
    if not get_user(userid):
        user_data = {
            "userid": userid,
            "plan": "Free",
            "valid_today": 0,
            "cycle_reset": datetime.utcnow(),
            "credits": 0,
            "last_batch_time": None,
            "is_admin": False
        }
        db.users.insert_one(user_data)
        return user_data
    return get_user(userid)

def update_user(userid, data: dict):
    """Actualiza datos de un usuario"""
    db.users.update_one({"userid": userid}, {"$set": data})

def increment_valid(userid, count=1):
    """Incrementa las tarjetas válidas usadas hoy"""
    user = get_user(userid)
    if user:
        new_count = user.get("valid_today", 0) + count
        update_user(userid, {"valid_today": new_count})

def reset_daily_limits():
    """Resetea los contadores diarios para usuarios que cumplen ciclo diario"""
    now = datetime.utcnow()
    users = db.users.find({"plan": {"$ne": "Ultra"}})
    for user in users:
        if user["cycle_reset"] <= now:
            update_user(user["userid"], {"valid_today": 0, "cycle_reset": now + timedelta(days=1)})

def can_process_lote(userid, max_lote, wait_seconds):
    """Verifica si un usuario puede enviar un lote según espera y límite de lote"""
    user = get_user(userid)
    now = datetime.utcnow()
    last_batch = user.get("last_batch_time")
    if last_batch:
        diff = (now - last_batch).total_seconds()
        if diff < wait_seconds:
            return False, wait_seconds - diff  # tiempo restante
    # Actualizar último batch
    update_user(userid, {"last_batch_time": now})
    return True, 0

# -------------------------------
# Funciones de plan
# -------------------------------

def get_plan_limits(userid):
    """Devuelve el límite de válidas según plan"""
    user = get_user(userid)
    plan = user.get("plan", "Free")
    from config.config import PLANS
    limits = PLANS.get(plan, PLANS["Free"])
    return limits["valid_limit"]

def is_admin(userid):
    """Verifica si el usuario es administrador"""
    user = get_user(userid)
    return user.get("is_admin", False)
