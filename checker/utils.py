import os
import stripe

# -------------------------------
# Configuración Stripe
# -------------------------------
stripe.api_key = os.getenv("STRIPE_API_KEY")  # Tu API Key de Stripe

def validate_card(card: str) -> str:
    """
    card = "4242424242424242|12|2026|123"  # formato: numero|mes|año|cvc
    Devuelve: "Life", "CVV" o "Invalid"
    """

    try:
        number, month, year, cvc = card.split("|")
        # Crear token de tarjeta en Stripe
        token = stripe.Token.create(
            card={
                "number": number,
                "exp_month": int(month),
                "exp_year": int(year),
                "cvc": cvc,
            }
        )
        # Si el token se crea sin errores → tarjeta válida
        return "Life"

    except stripe.error.CardError as e:
        # Error de la tarjeta → mapear según código
        code = e.code
        if code in ["incorrect_cvc", "incorrect_cvc_check"]:
            return "CVV"
        # Otros códigos → tarjeta inválida
        return "Invalid"

    except Exception as e:
        # Errores inesperados → tarjeta inválida
        print(f"Error validando tarjeta {card}: {e}")
        return "Invalid"
