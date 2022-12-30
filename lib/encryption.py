from bcrypt import hashpw, gensalt, checkpw
from os import urandom
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as padding_symmetric
from cryptography.hazmat.primitives.asymmetric import padding as padding_asymmetric
from cryptography.hazmat.backends import default_backend

def generate_key_pair() -> tuple[rsa.RSAPublicKey, rsa.RSAPrivateKey]:
    # Generate a 2048-bit RSA private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())    
    # Get the public key from the private key
    public_key = private_key.public_key()
    return public_key, private_key

def encrypt(plaintext: str, public_key: rsa.RSAPublicKey) -> bytes:
    # Convert the plaintext string to bytes
    plaintext_bytes = plaintext.encode()
    # Encrypt the plaintext using the RSA public key and PKCS1 padding
    ciphertext = public_key.encrypt(plaintext_bytes, padding_asymmetric.PKCS1v15())
    return ciphertext

def decrypt(ciphertext: bytes, private_key: rsa.RSAPrivateKey) -> str:
    # Decrypt the ciphertext using the RSA private key and PKCS1 padding
    plaintext_bytes = private_key.decrypt(ciphertext, padding_asymmetric.PKCS1v15())
    # Convert the decrypted bytes to a string
    plaintext = plaintext_bytes.decode()
    return plaintext

def hash_password(password: str) -> str:
    # Hash the password using the bcrypt algorithm
    hashed_password = hashpw(password.encode(), gensalt())
    return hashed_password.decode()

def verify_password(password: str, hashed_password: str) -> bool:
    # Verify the password against the hashed password
    is_password_correct = checkpw(password.encode(), hashed_password.encode())
    return is_password_correct

def generate_key(key) -> bytes:
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