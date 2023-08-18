from lib import database, encryption, utils
import os
import unittest

class test_encryption(unittest.TestCase):
    def test_generate_key_pair(self):
        encryption.generate_key_pair()
        # Check that the public key exists in the environment variables
        self.assertTrue(encryption.load_public_key())
        # Check that the private key file exists in environment variables
        self.assertTrue(encryption.load_private_key())
        encryption.delete_key_pair()
    
    def test_encrypt_symmetrical_key(self):
        encryption.generate_key_pair()
        public_key = encryption.load_public_key()
        symmetrical_key = encryption.generate_symmetrical_key("secret key")
        encrypted_symmetrical_key = encryption.encrypt_symmetrical_key(symmetrical_key)
        # Check that the encrypted symmetrical key is a bytes object
        self.assertIsInstance(encrypted_symmetrical_key, bytes)
        # Check that the encrypted symmetrical key is not empty
        self.assertTrue(encrypted_symmetrical_key)
        # Check that the encrypted symmetrical key is not the same as the original symmetrical key
        self.assertNotEqual(encrypted_symmetrical_key, symmetrical_key)
        encryption.delete_key_pair()
    
    def test_decrypt_symmetrical_key(self):
        encryption.generate_key_pair()
        public_key = encryption.load_public_key()
        private_key = encryption.load_private_key()
        symmetrical_key = encryption.generate_symmetrical_key("secret key")
        encrypted_symmetrical_key = encryption.encrypt_symmetrical_key(symmetrical_key)
        decrypted_symmetrical_key = encryption.decrypt_symmetrical_key(encrypted_symmetrical_key)
        # Check that the decrypted symmetrical key is a bytes object
        self.assertIsInstance(decrypted_symmetrical_key, bytes)
        # Check that the decrypted symmetrical key is not empty
        self.assertTrue(decrypted_symmetrical_key)
        # Check that the decrypted symmetrical key is the same as the original symmetrical key
        self.assertEqual(decrypted_symmetrical_key, symmetrical_key)
        encryption.delete_key_pair()
        
    def test_hash_password(self):
        hashed_password = encryption.hash_password("password")
        # Check that the hashed password is a string
        self.assertIsInstance(hashed_password, str)
        # Check that the hashed password is not empty
        self.assertTrue(hashed_password)
        # Check that the hashed password is not the same as the original password
        self.assertNotEqual(hashed_password, "password")
    
    def test_verify_password(self):
        hashed_password = encryption.hash_password("password")
        # Verify the password
        self.assertTrue(encryption.verify_password("password", hashed_password))
        # Check that the wrong password is not verified
        self.assertFalse(encryption.verify_password("notpassword", hashed_password))
    
    def test_generate_key(self):
        key = encryption.generate_symmetrical_key("secret key")
        # Check that the key is a bytes object
        self.assertIsInstance(key, bytes)
        # Check that the key is not empty
        self.assertTrue(key)
    
    def test_encrypt_password(self):
        key = encryption.generate_symmetrical_key("secret key")
        encrypted_password = encryption.encrypt_password("password", key)
        # Check that the encrypted password is a bytes object
        self.assertIsInstance(encrypted_password, bytes)
        # Check that the encrypted password is not empty
        self.assertTrue(encrypted_password)
        # Check that the encrypted password is not the same as the original password
        self.assertNotEqual(encrypted_password, "password".encode())
    
    def test_decrypt_password(self):
        key = encryption.generate_symmetrical_key("secret key")
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
        password = utils.generate_password(16)
        # Check that the password is a string
        self.assertIsInstance(password, str)
        # Check that the password is not empty
        self.assertTrue(password)
        # Check that the password is 16 characters long
        self.assertEqual(len(password), 16)
    
    def test_generate_user(self):
        username, hashed_password, symmetrical_key = utils.generate_user("test", "test")
        # check that the password has been hashed
        self.assertNotEqual(hashed_password, "test")
        # check that the password is not empty
        self.assertTrue(hashed_password)
        # check that the password is a string
        self.assertIsInstance(hashed_password, str)
        # check that the username is not empty
        self.assertTrue(username)
        # check that the username is a string
        self.assertIsInstance(username, str)
        # check that the symmetrical key is not empty
        self.assertTrue(symmetrical_key)
        # check that the symmetrical key is a bytes object
        self.assertIsInstance(symmetrical_key, bytes)
        
    def test_generate_random_entry(self):
        website, username, password = utils.generate_random_entry()
        # check that the website is not empty
        self.assertTrue(website)
        # check that the website is a string
        self.assertIsInstance(website, str)
        # check that the username is not empty
        self.assertTrue(username)
        # check that the username is a string
        self.assertIsInstance(username, str)
        # check that the password is not empty
        self.assertTrue(password)
        # check that the password is a string
        self.assertIsInstance(password, str)
    
    def test_make_test_users(self):
        db = database("test.db")
        db.add_users_table()
        db.add_services_table()
        encryption.generate_key_pair()
        utils.make_test_users(db, 10, 10)
        # Check that the users table exists
        self.assertTrue(db.table_exists("users"))
        # Check that the services table exists
        self.assertTrue(db.table_exists("services"))
        # Check that the users table has 10 entries
        self.assertEqual(db.count_table("users"), 10)
        # Check that the services table has 100 entries
        self.assertEqual(db.count_table("services"), 100)
        db.rm()
        encryption.delete_key_pair()
        
    def test_setup(self):
        utils.setup()
        db = database("data.db")
        # Check that the database exists
        self.assertTrue(db.database_exists())
        # Check that the users table exists
        self.assertTrue(db.table_exists("users"))
        # Check that the services table exists
        self.assertTrue(db.table_exists("services"))
        # Check that the encryption key pair exists
        self.assertTrue(encryption.load_private_key())
        self.assertTrue(encryption.load_public_key())
        db.rm()
        encryption.delete_key_pair()

class test_database(unittest.TestCase):
    def test_create_database(self):
        db = database("test.db")
        # Check that the database exists
        self.assertTrue(db.database_exists())
        db.rm()
    
    def test_add_users_table(self):
        db = database("test.db")
        db.add_users_table()
        # Check that the table exists
        self.assertTrue(db.table_exists("users"))
        db.rm()
    
    def test_add_services_table(self):
        db = database("test.db")
        db.add_services_table()
        # Check that the table exists
        self.assertTrue(db.table_exists("services"))
        db.rm()
    
    def test_add_user(self):
        db = database("test.db")
        db.add_users_table()
        db.add_user("test", "test","test".encode())
        # Check that the user exists
        self.assertTrue(db.find_user("test"))
        db.rm()
    
    def test_add_service(self):
        db = database("test.db")
        db.add_services_table()
        db.add_service("test", "test", "test".encode(), "test")
        # Check that the service exists
        self.assertTrue(db.find_service(1))
        db.rm()
    
    def test_delete_user(self):
        db = database("test.db")
        db.add_users_table()
        db.add_user("test", "test","test".encode())
        # Check that the user exists
        self.assertTrue(db.find_user("test"))
        db.delete_user("test")
        # Check that the user no longer exists
        self.assertFalse(db.find_user("test"))
        db.rm()
        
    def test_delete_service(self):
        db = database("test.db")
        db.add_services_table()
        db.add_service("test", "test", "test".encode(), "test")
        # Check that the service exists
        self.assertTrue(db.find_service(1))
        db.delete_service(1)
        # Check that the service no longer exists
        self.assertFalse(db.find_service(1))
        db.rm()
    
    def test_find_user(self):
        db = database("test.db")
        db.add_users_table()
        db.add_user("test", "test","test".encode())
        # Check that the user exists
        self.assertTrue(db.find_user("test"))
        db.rm()
    
    def test_find_service(self):
        db = database("test.db")
        db.add_services_table()
        db.add_service("test", "test", "test".encode(), "test")
        # Check that the service exists
        self.assertTrue(db.find_service(1))
        db.rm()
    
    def test_rollback(self):
        db = database("test.db")
        db.add_users_table()
        db.add_user("test", "test","test".encode())
        # Check that the user exists
        self.assertTrue(db.find_user("test"))
        db.rollback()
        # Check that the user no longer exists
        self.assertFalse(db.find_user("test"))
        db.rm()
    
    def test_commit(self):
        db = database("test.db")
        db.add_users_table()
        db.add_user("test", "test","test".encode())
        # Check that the user exists
        self.assertTrue(db.find_user("test"))
        db.commit()
        # Check that the user still exists after rollback
        db.rollback()
        self.assertTrue(db.find_user("test"))
        db.rm()
    
    def test_find_user_services(self):
        db = database("test.db")
        db.add_users_table()
        db.add_services_table()
        db.add_user("test", "test","test".encode())
        id = db.find_user("test")["id"]
        db.add_service("test", "test", "test".encode(), "test", id)
        db.add_service("test2", "test2", "test2".encode(), "test2", id)
        # Check that the services exists
        self.assertTrue(db.find_service(1))
        self.assertTrue(db.find_service(2))
        # Check that all services are returned
        self.assertEqual(len(db.find_user_services("test")), 2)
        db.rm()
    
    def test_search_user_services(self):
        db = database("test.db")
        db.add_users_table()
        db.add_services_table()
        db.add_user("test", "test","test".encode())
        id = db.find_user("test")["id"]
        db.add_service("test", "test", "test".encode(), "test", id)
        db.add_service("test2", "test2", "test2".encode(), "test2", id)
        # Check that the services exists
        self.assertTrue(db.find_service(1))
        self.assertTrue(db.find_service(2))
        # Check that all like services are returned
        self.assertEqual(len(db.search_user_services("test", "test")), 2)
        db.rm()
    
    def test_count_table(self):
        db = database("test.db")
        db.add_users_table()
        db.add_services_table()
        encryption.generate_key_pair()
        utils.make_test_users(db, 10, 10)
        # Check that the users table has 10 entries
        self.assertEqual(db.count_table("users"), 10)
        # Check that the services table has 100 entries
        self.assertEqual(db.count_table("services"), 100)
        db.rm()
        encryption.delete_key_pair()
    
    def test_rm(self):
        db = database("test.db")
        # Check that the database exists
        self.assertTrue(os.path.exists("test.db"))
        db.rm()
        # Check that the database no longer exists
        self.assertFalse(os.path.exists("test.db"))

# run the tests
if __name__ == "__main__":
    unittest.main()