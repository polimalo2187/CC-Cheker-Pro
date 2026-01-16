from config.config import PLANS
from database.mongo import get_user, update_user
from datetime import datetime, timedelta

# -------------------------------
# Funciones para planes
# -------------------------------

def get_user_plan(userid):
    """Obtiene el plan actual del usuario"""
    user = get_user(userid)
    if user:
        return user.get("plan", "Free")
    return "Free"

def activate_plan(userid, plan_name):
    """
    Activa un plan para un usuario:
    - Actualiza plan
    - Reinicia contadores de válidas
    - Configura ciclo de reinicio
    """
    if plan_name not in PLANS:
        return False, f"Plan '{plan_name}' no existe."

    user = get_user(userid)
    if not user:
        return False, "Usuario no registrado."

    # Configurar ciclo
    cycle_type = PLANS[plan_name]["cycle"]
    now = datetime.utcnow()
    if cycle_type == "daily":
        cycle_reset = now + timedelta(days=1)
    elif cycle_type == "monthly":
        cycle_reset = now + timedelta(days=30)
    else:
        cycle_reset = now

    data = {
        "plan": plan_name,
        "valid_today": 0,
        "cycle_reset": cycle_reset
    }

    # Para plan Ultra, los créditos son ilimitados
    if plan_name == "Ultra":
        data["credits"] = float("inf")
    else:
        data["credits"] = 0  # reset créditos al activar plan normal

    update_user(userid, data)
    return True, f"Plan '{plan_name}' activado correctamente."

def add_credits(userid, amount):
    """Agrega créditos adicionales a un usuario"""
    user = get_user(userid)
    if not user:
        return False, "Usuario no registrado."
    
    credits = user.get("credits", 0)
    # Si es Ultra, mantener ilimitado
    if user.get("plan") == "Ultra":
        credits = float("inf")
    else:
        credits += amount

    update_user(userid, {"credits": credits})
    return True, f"{amount} créditos agregados. Total ahora: {'∞' if credits == float('inf') else credits}."

def use_credit(userid):
    """Usa un crédito del usuario si tiene"""
    user = get_user(userid)
    if not user:
        return False, "Usuario no registrado."
    
    # Ultra tiene créditos ilimitados
    if user.get("plan") == "Ultra":
        return True, "Crédito usado. Créditos restantes: ∞"

    credits = user.get("credits", 0)
    if credits <= 0:
        return False, "No tienes créditos disponibles."
    
    update_user(userid, {"credits": credits - 1})
    return True, f"Crédito usado. Créditos restantes: {credits - 1}"

def check_cycle_reset(userid):
    """Verifica si el ciclo del usuario terminó y resetea válidas si aplica"""
    user = get_user(userid)
    if not user:
        return False
    
    now = datetime.utcnow()
    if user.get("cycle_reset") and user["cycle_reset"] <= now:
        # Reinicia contador de válidas
        update_user(userid, {"valid_today": 0})
        
        # Reinicia créditos si no es Ultra
        if user.get("plan") != "Ultra":
            update_user(userid, {"credits": 0})

        # Calcula siguiente ciclo
        plan_name = user.get("plan", "Free")
        cycle_type = PLANS[plan_name]["cycle"]
        if cycle_type == "daily":
            next_cycle = now + timedelta(days=1)
        elif cycle_type == "monthly":
            next_cycle = now + timedelta(days=30)
        else:
            next_cycle = now
        update_user(userid, {"cycle_reset": next_cycle})
        return True
    return False
