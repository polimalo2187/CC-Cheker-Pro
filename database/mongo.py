from pymongo import MongoClient
from datetime import datetime, timedelta
import os
import string
import random

# ==================================================
# Configuración de conexión MongoDB
# ==================================================
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["checkerbot_db"]
users_col = db["users"]

# ==================================================
# Funciones de usuario
# ==================================================
def generate_ref_code(length=6):
    """Genera un código alfanumérico único"""
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    while users_col.find_one({"ref_code": code}):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return code

def add_user(user_id: int, ref_code=None):
    """Agregar un nuevo usuario a la base de datos"""
    if users_col.find_one({"user_id": user_id}):
        return False  # Usuario ya existe

    if not ref_code:
        ref_code = generate_ref_code()

    user_data = {
        "user_id": user_id,
        "plan": "Free",
        "plan_expiry": None,
        "credits": 0,
        "ref_code": ref_code,
        "referred_by": None,
        "valid_referrals": [],
        "registered_on": datetime.utcnow(),
        "last_check": None,
        "valid_today": 0,
        "cycle_reset": None
    }
    users_col.insert_one(user_data)
    return True

def get_user(user_id: int):
    """Obtener usuario por ID"""
    return users_col.find_one({"user_id": user_id})

def get_all_users():
    """Obtener todos los usuarios"""
    return list(users_col.find())

def update_user(user_id: int, update_dict: dict):
    """Actualizar datos de un usuario"""
    users_col.update_one({"user_id": user_id}, {"$set": update_dict})

def increment_credits(user_id: int, amount: int):
    """Sumar créditos a un usuario"""
    user = get_user(user_id)
    if not user:
        return False
    new_credits = user.get("credits", 0) + amount
    update_user(user_id, {"credits": new_credits})
    return True

def add_referral_to_user(referrer_id: int, referred_user_id: int, plan: str):
    """Agregar un referido a un usuario"""
    referral = {
        "user_id": referred_user_id,
        "plan": plan,
        "date": datetime.utcnow()
    }
    users_col.update_one(
        {"user_id": referrer_id},
        {"$push": {"valid_referrals": referral}}
    )

def update_plan(user_id: int, plan: str, months: int = 1):
    """Actualizar plan y fecha de expiración"""
    user = get_user(user_id)
    if not user:
        return False

    now = datetime.utcnow()
    current_expiry = user.get("plan_expiry")

    if current_expiry and current_expiry > now:
        new_expiry = current_expiry + timedelta(days=30 * months)
    else:
        new_expiry = now + timedelta(days=30 * months)

    update_user(user_id, {"plan": plan, "plan_expiry": new_expiry})

# ==================================================
# Funciones de referidos y créditos automáticos
# ==================================================
def apply_referral(new_user_id: int, ref_code: str):
    """Aplica los créditos por referido"""
    if not ref_code:
        return False

    # Buscar al usuario que tenga el código
    referrer = users_col.find_one({"ref_code": ref_code})
    if not referrer or referrer["user_id"] == new_user_id:
        return False  # Código inválido o se refiere a sí mismo

    # Registrar referido
    new_user = get_user(new_user_id)
    update_user(new_user_id, {"referred_by": ref_code})

    # Calcular créditos según plan del referido
    plan = new_user.get("plan", "Free")
    if plan == "Free":
        credit = 1
    elif plan == "Basic":
        credit = 10
    elif plan == "Pro":
        credit = 25
    elif plan == "Ultra":
        credit = 50
    else:
        credit = 0

    # Sumar créditos al referidor
    increment_credits(referrer["user_id"], credit)

    # Registrar referido en la lista del referidor
    add_referral_to_user(referrer["user_id"], new_user_id, plan)
    return True

# ==================================================
# Estadísticas globales
# ==================================================
def total_users():
    return users_col.count_documents({})

def total_credits():
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$credits"}}}
    ]
    result = list(users_col.aggregate(pipeline))
    return result[0]["total"] if result else 0
