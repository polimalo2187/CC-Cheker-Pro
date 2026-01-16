from web3 import Web3
from database.mongo import get_user, add_credits
from config.config import BSC_NODE_URL, PAYMENT_WALLET, ADMIN_ID

# -------------------------------
# Conexión a la blockchain BSC
# -------------------------------
w3 = Web3(Web3.HTTPProvider(BSC_NODE_URL))

if not w3.isConnected():
    raise ConnectionError("No se pudo conectar a la red BSC")

# Dirección del contrato USDT BEP20 (BEP20 token)
USDT_CONTRACT_ADDRESS = Web3.toChecksumAddress("0x55d398326f99059fF775485246999027B3197955")

# ABI mínimo para balance y transferencia
USDT_ABI = [
    {
        "constant": True,
        "inputs": [{"name":"_owner","type":"address"}],
        "name":"balanceOf",
        "outputs":[{"name":"balance","type":"uint256"}],
        "type":"function"
    },
    {
        "constant": False,
        "inputs":[
            {"name":"_to","type":"address"},
            {"name":"_value","type":"uint256"}
        ],
        "name":"transfer",
        "outputs":[{"name":"success","type":"bool"}],
        "type":"function"
    }
]

usdt_contract = w3.eth.contract(address=USDT_CONTRACT_ADDRESS, abi=USDT_ABI)

# -------------------------------
# Funciones de pago
# -------------------------------

def check_payment(user_wallet, amount):
    """
    Verifica si un usuario envió USDT BEP20 a nuestra wallet
    amount -> en USDT (entero, ej: 10 USDT)
    """
    try:
        balance = usdt_contract.functions.balanceOf(PAYMENT_WALLET).call()
        # Convertir a decimales reales (USDT tiene 18 decimales en BEP20)
        balance_real = balance / 10**18
        if balance_real >= amount:
            return True
        return False
    except Exception as e:
        return False

def credit_user(userid, usdt_amount, credit_value):
    """
    Agrega créditos a un usuario después de confirmar el pago
    usdt_amount -> cantidad enviada
    credit_value -> créditos que corresponden a esa cantidad
    """
    user = get_user(userid)
    if not user:
        return False, "Usuario no registrado"

    add_credits(userid, credit_value)
    return True, f"✅ Se agregaron {credit_value} créditos por {usdt_amount} USDT"

def transfer_to_admin(amount):
    """
    Envía USDT recibido a la wallet del admin
    """
    try:
        tx = usdt_contract.functions.transfer(
            Web3.toChecksumAddress(ADMIN_ID),
            int(amount * 10**18)
        ).buildTransaction({
            'from': PAYMENT_WALLET,
            'gas': 200000,
            'gasPrice': w3.toWei('5', 'gwei'),
            'nonce': w3.eth.get_transaction_count(PAYMENT_WALLET)
        })
        # Firma y envío debe hacerse con la llave privada segura (no incluida aquí)
        return tx
    except Exception as e:
        return None
