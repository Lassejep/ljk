from lib import encryption, utils, database
import unittest

class test_encryption(unittest.TestCase):
    def test_generate_key_pair(self):
        # Generate a key pair
        public_key, private_key = encryption.generate_key_pair()
        # Check that the public key is an instance of rsa.RSAPublicKey
        self.assertIsInstance(public_key, encryption.rsa.RSAPublicKey)
        # Check that the private key is an instance of rsa.RSAPrivateKey
        self.assertIsInstance(private_key, encryption.rsa.RSAPrivateKey)
    
    def test_encrypt(self):
        # Generate a key pair
        public_key, private_key = encryption.generate_key_pair()
        # Encrypt a plaintext
        ciphertext = encryption.encrypt("Hello, world!", public_key)
        # Check that the ciphertext is a bytes object
        self.assertIsInstance(ciphertext, bytes)
        # Check that the ciphertext is not empty
        self.assertTrue(ciphertext)
        # Check that the ciphertext is not the same as the plaintext
        self.assertNotEqual(ciphertext, "Hello, world!".encode())
    
    def test_decrypt(self):
        # Generate a key pair
        public_key, private_key = encryption.generate_key_pair()
        # Encrypt a plaintext
        ciphertext = encryption.encrypt("Hello, world!", public_key)
        # Decrypt the ciphertext
        plaintext = encryption.decrypt(ciphertext, private_key)
        # Check that the plaintext is a string
        self.assertIsInstance(plaintext, str)
        # Check that the plaintext is not empty
        self.assertTrue(plaintext)
        # Check that the plaintext is the same as the original plaintext
        self.assertEqual(plaintext, "Hello, world!")
        
    def test_hash_password(self):
        # Hash a password
        hashed_password = encryption.hash_password("password")
        # Check that the hashed password is a string
        self.assertIsInstance(hashed_password, str)
        # Check that the hashed password is not empty
        self.assertTrue(hashed_password)
        # Check that the hashed password is not the same as the original password
        self.assertNotEqual(hashed_password, "password")
    
    def test_verify_password(self):
        # Hash a password
        hashed_password = encryption.hash_password("password")
        # Verify the password
        self.assertTrue(encryption.verify_password("password", hashed_password))
        # Check that the wrong password is not verified
        self.assertFalse(encryption.verify_password("notpassword", hashed_password))
    
    def test_generate_key(self):
        # Generate a key
        key = encryption.generate_key("secret key")
        # Check that the key is a bytes object
        self.assertIsInstance(key, bytes)
        # Check that the key is not empty
        self.assertTrue(key)
    
    def test_encrypt_password(self):
        key = encryption.generate_key("secret key")
        encrypted_password = encryption.encrypt_password("password", key)
        # Check that the encrypted password is a bytes object
        self.assertIsInstance(encrypted_password, bytes)
        # Check that the encrypted password is not empty
        self.assertTrue(encrypted_password)
        # Check that the encrypted password is not the same as the original password
        self.assertNotEqual(encrypted_password, "password".encode())
    
    def test_decrypt_password(self):
        key = encryption.generate_key("secret key")
        encrypted_password = encryption.encrypt_password("password", key)
        decrypted_password = encryption.decrypt_password(encrypted_password, key)
        # Check that the decrypted password is a string
        self.assertIsInstance(decrypted_password, str)
        # Check that the decrypted password is not empty
        self.assertTrue(decrypted_password)
        # Check that the decrypted password is the same as the original password
        self.assertEqual(decrypted_password, "password")

class test_utils(unittest.TestCase):
    def test_generate_password(self):
        # Generate a password
        password = utils.generate_password(16)
        # Check that the password is a string
        self.assertIsInstance(password, str)
        # Check that the password is not empty
        self.assertTrue(password)
        # Check that the password is 16 characters long
        self.assertEqual(len(password), 16)

# run the tests
if __name__ == "__main__":
    unittest.main()