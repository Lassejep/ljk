from secrets import choice, randbits
from string import ascii_letters, digits, punctuation
from typing import Optional

import argon2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_password(password_length: int = 16) -> str:
    return "".join(
        choice(ascii_letters + digits + punctuation) for _ in range(password_length)
    )


def hash_password(password: str) -> str:
    return argon2.PasswordHasher().hash(password)


def verify_password(password: str, hash: str) -> bool:
    try:
        return argon2.PasswordHasher().verify(hash, password)
    except argon2.exceptions.VerifyMismatchError:
        return False
    except Exception as e:
        print(e)
        return False


def generate_vault_key() -> bytes:
    return AESGCM.generate_key(256)


def create_mkey(password: str, dkey: bytes) -> bytes:
    salt = dkey
    kdf = argon2.PasswordHasher(
        time_cost=16, memory_cost=65536, parallelism=8, hash_len=32, salt_len=32
    )
    hash = kdf.hash(password, salt=salt)
    return hash[-32:].encode()


def create_dkey(password: str, username: str) -> bytes:
    if len(username) < 8:
        raise ValueError("Username must be at least 8 characters long")
    salt = username.encode()
    kdf = argon2.PasswordHasher(
        time_cost=16, memory_cost=65536, parallelism=8, hash_len=32, salt_len=len(salt)
    )
    hash = kdf.hash(password, salt=salt)
    return hash[-32:].encode()


def encrypt(
    plaintext: bytes, key: bytes, associated_data: Optional[bytes] = None
) -> bytes:
    nonce = randbits(96).to_bytes(12, "big")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data)
    return nonce + ciphertext


def decrypt(
    ciphertext: bytes, key: bytes, associated_data: Optional[bytes] = None
) -> bytes:
    nonce = ciphertext[:12]
    ciphertext = ciphertext[12:]
    return AESGCM(key).decrypt(nonce, ciphertext, associated_data)
