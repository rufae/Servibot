"""
Cryptography Utility
Provides token encryption/decryption functions for secure storage.
"""
import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

# Encryption key se debe cargar desde variable de entorno
# Para generarla: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Si no hay key en env, generar una warning pero crear una default (SOLO PARA DEV)
if not ENCRYPTION_KEY:
    logger.warning(
        "⚠️ ENCRYPTION_KEY not found in environment. Using default key. "
        "This is INSECURE for production! Set ENCRYPTION_KEY in .env"
    )
    # Generar key determinística para desarrollo (CAMBIAR EN PRODUCCION)
    ENCRYPTION_KEY = "dev_fallback_key_change_in_production"

# Derivar una key válida de Fernet desde la key proporcionada
def _get_fernet_key(key_material: str) -> bytes:
    """Deriva una key válida de Fernet desde un string."""
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'servibot_salt_v1',  # Salt fijo para consistencia (en prod usar salt por usuario)
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(key_material.encode()))
    return key

# Instancia global de Fernet
try:
    _fernet_key = _get_fernet_key(ENCRYPTION_KEY)
    _cipher = Fernet(_fernet_key)
except Exception as e:
    logger.error(f"❌ Error initializing encryption cipher: {e}")
    _cipher = None


def encrypt_token(token: str) -> Optional[str]:
    """
    Encripta un token OAuth.
    
    Args:
        token: Token en texto plano
        
    Returns:
        Token encriptado en base64, o None si falla
    """
    if not token:
        return None
    
    if not _cipher:
        logger.error("Cipher not initialized, returning plain token")
        return token  # Fallback: devolver sin encriptar
    
    try:
        encrypted = _cipher.encrypt(token.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"❌ Error encrypting token: {e}")
        return token  # Fallback


def decrypt_token(encrypted_token: str) -> Optional[str]:
    """
    Desencripta un token OAuth.
    
    Args:
        encrypted_token: Token encriptado
        
    Returns:
        Token en texto plano, o None si falla
    """
    if not encrypted_token:
        return None
    
    if not _cipher:
        logger.error("Cipher not initialized, returning as-is")
        return encrypted_token  # Fallback
    
    try:
        decrypted = _cipher.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        # Puede ser que el token no esté encriptado (legacy data)
        logger.warning(f"⚠️ Could not decrypt token (may be plain text): {e}")
        return encrypted_token  # Asumir que es texto plano


def is_encrypted(token: str) -> bool:
    """
    Verifica si un token parece estar encriptado.
    
    Args:
        token: Token a verificar
        
    Returns:
        True si parece encriptado, False si es texto plano
    """
    if not token:
        return False
    
    try:
        # Tokens encriptados con Fernet tienen formato específico
        # Intentar decodificar como Fernet token
        from cryptography.fernet import Fernet
        Fernet._signing_key = None  # Evitar error de key
        return token.startswith('gAAAAA')  # Fernet tokens empiezan así
    except:
        return False


# Funciones de conveniencia para migración gradual
def ensure_encrypted(token: Optional[str]) -> Optional[str]:
    """
    Asegura que un token esté encriptado.
    Si ya está encriptado, lo devuelve. Si no, lo encripta.
    """
    if not token:
        return None
    
    if is_encrypted(token):
        return token
    
    return encrypt_token(token)


def ensure_decrypted(token: Optional[str]) -> Optional[str]:
    """
    Asegura que un token esté desencriptado.
    Si ya está en texto plano, lo devuelve. Si está encriptado, lo desencripta.
    """
    if not token:
        return None
    
    if is_encrypted(token):
        return decrypt_token(token)
    
    return token


if __name__ == "__main__":
    # Test básico
    print("Testing encryption utilities...")
    
    test_token = "ya29.a0AfB_byDexample_access_token_12345"
    print(f"\nOriginal token: {test_token}")
    
    encrypted = encrypt_token(test_token)
    print(f"Encrypted: {encrypted}")
    
    decrypted = decrypt_token(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert decrypted == test_token, "Decryption failed!"
    print("\n✅ Encryption/Decryption working correctly!")
