from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from string import ascii_letters, digits, punctuation
from secrets import choice, randbits


def generate_password(password_length=16):
    password = ''.join(
        choice(ascii_letters + digits + punctuation)
        for _ in range(password_length)
    )
    return password


def hash_password(password):
    return PasswordHasher().hash(password)


def verify_password(password, hash):
    try:
        return PasswordHasher().verify(hash, password)
    except VerifyMismatchError:
        return False
    except Exception as e:
        print(e)
        return False


def generate_vault_key():
    return AESGCM.generate_key(bit_length=256)


def generate_salt():
    return randbits(256).to_bytes(32, "big")


def create_data_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())


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
