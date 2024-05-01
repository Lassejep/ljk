import unittest
import os
from src import encryption


class TestEncryption(unittest.TestCase):
    def test_generate_password(self):
        password = encryption.generate_password()
        self.assertEqual(len(password), 16)
        password = encryption.generate_password(20)
        self.assertEqual(len(password), 20)

    def test_hash_password(self):
        password = "test_password"
        hashed_password = encryption.hash_password(password)
        self.assertNotEqual(password, hashed_password)
        hashed_password_2 = encryption.hash_password(password)
        self.assertNotEqual(hashed_password, hashed_password_2)

    def test_verify_password(self):
        password = "test_password"
        hashed_password = encryption.hash_password(password)
        self.assertTrue(encryption.verify_password(password, hashed_password))
        self.assertFalse(encryption.verify_password(
            "wrong_password", hashed_password)
        )

    def test_generate_vault_key(self):
        key = encryption.generate_vault_key()
        self.assertEqual(len(key), 32)

    def test_generate_salt(self):
        salt = encryption.generate_salt()
        self.assertEqual(len(salt), 32)

    def test_create_data_key(self):
        password = "test_password"
        salt = encryption.generate_salt()
        data_key = encryption.create_data_key(password, salt)
        self.assertEqual(len(data_key), 32)

    def test_encrypt(self):
        key = encryption.generate_vault_key()
        data = "test_data".encode()
        encrypted_data = encryption.encrypt(data, key)
        self.assertNotEqual(data, encrypted_data)

    def test_decrypt(self):
        key = encryption.generate_vault_key()
        data = "test_data".encode()
        encrypted_data = encryption.encrypt(data, key)
        decrypted_data = encryption.decrypt(encrypted_data, key)
        self.assertEqual(data, decrypted_data)

    def test_encrypt_file(self):
        key = encryption.generate_vault_key()
        file_path = "test_file.txt"
        with open(file_path, "w") as file:
            file.write("test_data")
        encrypted_data = encryption.encrypt_file(file_path, key)
        self.assertNotEqual("test_data", encrypted_data)
        os.remove(file_path)

    def test_decrypt_file(self):
        key = encryption.generate_vault_key()
        file_path = "test_file.txt"
        encrypted_file_path = "test_file_encrypted.txt"
        with open(file_path, "w") as file:
            file.write("test_data")
        encrypted_data = encryption.encrypt_file(file_path, key)
        with open(encrypted_file_path, "wb") as encrypted_file:
            encrypted_file.write(encrypted_data)
        self.assertNotEqual("test_data", encrypted_data)
        encryption.decrypt_file(encrypted_file_path, key)
        with open(file_path, "r") as file:
            decrypted_data = file.read()
        self.assertEqual("test_data", decrypted_data)
        os.remove(file_path)
        os.remove(encrypted_file_path)
