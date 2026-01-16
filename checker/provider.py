import os

class CheckerProviderError(Exception):
    pass


class CheckerProvider:
    """
    Esta clase define la interfaz REAL del checker.
    No hay simulaciones.
    Tú conectas aquí tu backend o gateway permitido.
    """

    def __init__(self):
        self.sk_key = os.getenv("SK_KEY")
        if not self.sk_key:
            raise CheckerProviderError("SK_KEY no definida en variables de entorno")

    def check_card(self, number: str, month: str, year: str, cvc: str) -> str:
        """
        Debe devolver UNO de estos valores:
        - LIVE
        - CVV
        - DEAD

        Implementación REAL requerida.
        """
        raise NotImplementedError(
            "Debes implementar check_card() con tu proveedor real"
        )
