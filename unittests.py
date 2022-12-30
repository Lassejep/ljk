from lib import encryption, utils, database
import unittest

class TestPasswordManager(unittest.TestCase):
    def test_generate_password(self):
        # Test that the generated password is the correct length
        password = utils.generate_password(10)
        self.assertEqual(len(password), 10)
        # Test that the generated password is different each time
        password2 = utils.generate_password(10)
        self.assertNotEqual(password, password2)
    
    def test_encrypt_decrypt(self):
        private_key = encryption.rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        # Test that the encrypt function returns a bytes object
        ciphertext = encryption.encrypt("secret message", public_key)
        self.assertIsInstance(ciphertext, bytes)
        # Test that the encrypted message can be decrypted using the private key
        plaintext = encryption.decrypt(ciphertext, private_key)
        self.assertEqual(plaintext, "secret message")
        
    def test_hash_password(self):
        # Test that the hashed password is different from the original password
        password = "password"
        hashed_password = encryption.hash_password(password)
        self.assertNotEqual(password, hashed_password)
    
    def test_verify_password(self):
        # Test that the correct password is verified
        password = "password"
        hashed_password = encryption.hash_password(password)
        is_password_correct = encryption.verify_password(password, hashed_password)
        self.assertTrue(is_password_correct)
        # Test that an incorrect password is not verified
        is_password_correct = encryption.verify_password("incorrect", hashed_password)
        self.assertFalse(is_password_correct)
    
    def test_encrypt_password(self):
        # Test that the encrypted password is different from the original password
        password = 'password123'
        key = b'1234567890123456'
        result = encryption.encrypt_password(password, key)
        self.assertIsInstance(result, bytes)
        self.assertNotEqual(result, password.encode())
        
    def test_decrypt_password(self):
        # Test that the decrypted password is the same as the original password
        password = 'password123'
        key = b'1234567890123456'
        encrypted_password = encryption.encrypt_password(password, key)
        result = encryption.decrypt_password(encrypted_password, key)
        self.assertEqual(result, password)

if __name__ == "__main__":
    unittest.main()
