import unittest
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

    def test_create_dkey(self):
        password = "test_password"
        username = "test_username"
        dkey = encryption.create_dkey(password, username)
        self.assertNotEqual(password, dkey)

    def test_create_mkey(self):
        password = "test_password"
        username = "test_username"
        dkey = encryption.create_dkey(password, username)
        mkey = encryption.create_mkey(password, dkey)
        self.assertNotEqual(password, mkey)
        self.assertNotEqual(dkey, mkey)

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
