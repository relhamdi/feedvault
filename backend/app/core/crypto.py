import json

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _get_fernet() -> Fernet:
    return Fernet(settings.fernet_key.encode())


def encrypt_credentials(data: dict) -> bytes:
    """Serialize data as JSON, then encrypt it using Fernet.

    Args:
        data (dict): Dict to encrypt.

    Returns:
        bytes: Encrypted dict.
    """
    raw = json.dumps(data).encode()
    return _get_fernet().encrypt(raw)


def decrypt_credentials(token: bytes) -> dict:
    """Parses token and deserialize the JSON.

    Args:
        token (bytes): Token to parse.

    Raises:
        InvalidToken: Raised if the token is corrupted or if the key has changed.

    Returns:
        dict: Deserialized dict.
    """
    try:
        raw = _get_fernet().decrypt(token)
    except InvalidToken as e:
        raise InvalidToken(
            "Unable to decrypt credentials: invalid key or corrupted token."
        ) from e
    return json.loads(raw)
