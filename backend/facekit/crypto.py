import os
from typing import List
from cryptography.fernet import Fernet, MultiFernet


def _load_keys() -> List[bytes]:
    keys_env = os.getenv("ENCRYPTION_KEYS", "")
    keys = [k.strip() for k in keys_env.split(",") if k.strip()]
    if not keys:
        raise RuntimeError("ENCRYPTION_KEYS environment variable not set")
    return [k.encode() for k in keys]


def _build_fernet() -> MultiFernet:
    key_bytes = _load_keys()
    fernets = [Fernet(k) for k in key_bytes]
    return MultiFernet(fernets)


FERNET = _build_fernet()


def encrypt(data: bytes) -> bytes:
    return FERNET.encrypt(data)


def decrypt(token: bytes) -> bytes:
    return FERNET.decrypt(token)


def refresh_keys() -> None:
    global FERNET
    FERNET = _build_fernet()
