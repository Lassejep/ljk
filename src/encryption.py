from bcrypt import hashpw, gensalt, checkpw
from os import urandom
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as padding_symmetric
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def hash_password(password):
    return hashpw(password.encode(), gensalt())


def verify_password(password, hash):
    return checkpw(password.encode(), hash)


def generate_random_key():
    return urandom(32)


def generate_salt():
    return urandom(32)


def generate_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())


def encrypt(key, plaintext):
    iv = urandom(16)
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    padder = padding_symmetric.PKCS7(256).padder()
    padded_plaintext = padder.update(plaintext) + padder.finalize()
    return iv + encryptor.update(padded_plaintext) + encryptor.finalize()


def decrypt(key, ciphertext):
    iv = ciphertext[:16]
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    unpadder = padding_symmetric.PKCS7(256).unpadder()
    padded_plaintext = decryptor.update(ciphertext[16:]) + decryptor.finalize()
    return unpadder.update(padded_plaintext) + unpadder.finalize()


def encrypt_file(key, filepath):
    with open(filepath, "rb") as f:
        plaintext = f.read()
    ciphertext = encrypt(key, plaintext)
    return ciphertext


def decrypt_file(key, filepath):
    with open(filepath, "rb") as f:
        ciphertext = f.read()
    plaintext = decrypt(key, ciphertext)
    with open(filepath, "wb") as f:
        f.write(plaintext)
