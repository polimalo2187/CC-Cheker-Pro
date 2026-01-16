import os

class CheckerProviderError(Exception):
    pass


class CheckerProvider:
    """
    Esta clase define la interfaz REAL del checker.
    No hay simulaciones.
    Conecta aquí tu backend o gateway permitido (ej. Stripple).
    """

    def __init__(self):
        self.sk_key = os.getenv("SK_KEY")
        if not self.sk_key:
            raise CheckerProviderError("SK_KEY no definida en variables de entorno")

    def check_card(self, number: str, month: str, year: str, cvc: str) -> str:
        """
        Debe devolver UNO de estos valores:
        - "LIVE"  -> tarjeta totalmente válida
        - "CVV"   -> número válido pero CVV incorrecto
        - "DEAD"  -> tarjeta inválida

        Implementación REAL requerida según tu proveedor.
        Ejemplo con Stripple: crear token o charge mínimo y mapear resultados.
        """
        # Aquí iría la integración real con Stripple u otro proveedor.
        # Puedes usar requests o su SDK oficial para validar la tarjeta.
        raise NotImplementedError(
            "Debes implementar check_card() con tu proveedor real"
        )
