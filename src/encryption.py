from bcrypt import hashpw, gensalt, checkpw
from os import urandom
from typing import Any
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as padding_symmetric
from cryptography.hazmat.primitives.asymmetric import padding as padding_asymmetric
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv, find_dotenv, set_key, get_key, unset_key

def generate_key_pair() -> None:
    # Generate a 2048-bit RSA private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())    
    # Get the public key from the private key
    public_key = private_key.public_key()
    load_dotenv(find_dotenv())
    set_key(find_dotenv(), "PRIVATE_KEY", private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption()).decode())
    # save public key to os environment variable
    set_key(find_dotenv(), "PUBLIC_KEY", public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode())

def delete_key_pair() -> None:
    # Delete the key pair from the given file
    load_dotenv(find_dotenv())
    unset_key(find_dotenv(), "PRIVATE_KEY")
    unset_key(find_dotenv(), "PUBLIC_KEY")

def load_public_key() -> Any:
    # Load the public key from the given file
    load_dotenv(find_dotenv())
    public_key: Any= get_key(find_dotenv(), "PUBLIC_KEY")
    # Convert the public key from a string to a public key object
    public_key = serialization.load_pem_public_key(public_key.encode(), backend=default_backend())
    return public_key

def load_private_key() -> Any:
    # Load the private key from the given file
    load_dotenv(find_dotenv())
    private_key: Any= get_key(find_dotenv(), "PRIVATE_KEY")
    # Convert the private key from a string to a private key object
    private_key = serialization.load_pem_private_key(private_key.encode(), password=None, backend=default_backend())
    return private_key

def encrypt_symmetrical_key(symmetrical_key: bytes) -> bytes:
    # Encrypt the symmetrical key using the RSA public key and PKCS1 padding
    public_key = load_public_key()
    encrypted_symmetrical_key = public_key.encrypt(symmetrical_key, padding_asymmetric.PKCS1v15())
    return encrypted_symmetrical_key

def decrypt_symmetrical_key(encrypted_symmetrical_key: bytes) -> bytes:
    # Decrypt the ciphe symmetrical key using the RSA private key and PKCS1 padding
    private_key = load_private_key()
    symmetrical_key = private_key.decrypt(encrypted_symmetrical_key, padding_asymmetric.PKCS1v15())
    return symmetrical_key

def hash_password(password: str) -> str:
    # Hash the password using the bcrypt algorithm
    hashed_password = hashpw(password.encode(), gensalt())
    return hashed_password.decode()

def verify_password(password: str, hashed_password: str) -> bool:
    # Verify the password against the hashed password
    is_password_correct = checkpw(password.encode(), hashed_password.encode())
    return is_password_correct

def generate_symmetrical_key(key) -> bytes:
    # Generate a 256-bit key from the given key
    key = key.encode()
    key = key + b'\x00' * (32 - len(key))
    return key

def encrypt_password(password: str, key: bytes) -> bytes:
    block_size = 128
    # Generate a random initialization vector (IV)
    iv = urandom(block_size // 8)
    # Create the cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    # Pad the password
    padder = padding_symmetric.PKCS7(block_size).padder()
    padded_password = padder.update(password.encode()) + padder.finalize()
    # Encrypt the padded password
    encrypted_password = encryptor.update(padded_password) + encryptor.finalize()
    # Return the IV and encrypted password
    return iv + encrypted_password

def decrypt_password(encrypted_password: bytes, key: bytes) -> str:
    block_size = 128
    # Extract the IV from the encrypted password
    iv = encrypted_password[:block_size // 8]
    # Create the cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    # Decrypt the padded password
    padded_password = decryptor.update(encrypted_password[block_size // 8:]) + decryptor.finalize()
    # Unpad the password
    unpadder = padding_symmetric.PKCS7(block_size).unpadder()
    password = unpadder.update(padded_password) + unpadder.finalize()
    # Return the decrypted password as a string
    return password.decode()