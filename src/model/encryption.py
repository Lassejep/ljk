from secrets import choice, randbits
from string import ascii_letters, digits, punctuation

import argon2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_password(password_length=16):
    password = "".join(
        choice(ascii_letters + digits + punctuation) for _ in range(password_length)
    )
    return password


def hash_password(password):
    return argon2.PasswordHasher().hash(password)


def verify_password(password, hash):
    try:
        return argon2.PasswordHasher().verify(hash, password)
    except argon2.exceptions.VerifyMismatchError:
        return False
    except Exception as e:
        print(e)
        return False


def generate_vault_key():
    return AESGCM.generate_key(bit_length=256)


def create_mkey(password, dkey):
    salt = dkey
    kdf = argon2.PasswordHasher(
        time_cost=16, memory_cost=65536, parallelism=8, hash_len=32, salt_len=32
    )
    hash = kdf.hash(password, salt=salt)
    return hash[-32:].encode()


def create_dkey(password, username):
    if len(username) < 8:
        raise ValueError("Username must be at least 8 characters long")
    salt = username.encode()
    kdf = argon2.PasswordHasher(
        time_cost=16, memory_cost=65536, parallelism=8, hash_len=32, salt_len=len(salt)
    )
    hash = kdf.hash(password, salt=salt)
    return hash[-32:].encode()


def encrypt(plaintext, key, associated_data=None):
    aesgcm = AESGCM(key)
    nonce = randbits(96).to_bytes(12, "big")
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return nonce + ciphertext


def decrypt(ciphertext, key, associated_data=None):
    aesgcm = AESGCM(key)
    nonce = ciphertext[:12]
    ciphertext = ciphertext[12:]
    return aesgcm.decrypt(nonce, ciphertext, associated_data)
