import unittest
import os
from src import db


class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_file = "test.db"
        self.db = db.Database(self.db_file)
        self.user_email = "test_user"
        self.user_auth_key = "test_auth_key"

    def tearDown(self):
        self.db.close()
        os.remove(self.db_file)

    def test_add_user(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        user = self.db.get_user(id)
        self.db.add_user("test_user_2", "test_auth_key_2")
        id2 = self.db.get_id("test_user_2")
        user2 = self.db.get_user(id2)
        self.assertIsNotNone(id)
        self.assertEqual(user["email"], self.user_email)
        self.assertEqual(user["auth_key"], self.user_auth_key)
        self.assertRaises(
            Exception, self.db.add_user, self.user_email, self.user_auth_key
        )
        self.assertIsNotNone(id2)
        self.assertEqual(user2["email"], "test_user_2")
        self.assertEqual(user2["auth_key"], "test_auth_key_2")
        self.assertRaises(
            Exception, self.db.add_user, "test_user_2", "test_auth_key"
        )
        self.assertNotEqual(id, id2)
        self.assertNotEqual(user["email"], user2["email"])
        self.assertNotEqual(user["auth_key"], user2["auth_key"])

    def test_delete_user(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.assertIsNotNone(id)
        self.db.delete_user(id)
        self.assertRaises(Exception, self.db.get_id, self.user_email)

    def test_get_user(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        user = self.db.get_user(id)
        self.assertEqual(user["email"], self.user_email)
        self.assertEqual(user["auth_key"], self.user_auth_key)
        self.assertRaises(Exception, self.db.get_user, 2)

    def test_update_email(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.update_email(id, "new_email", self.user_auth_key)
        user = self.db.get_user(id)
        self.assertEqual(user["email"], "new_email")
        self.assertNotEqual(user["email"], self.user_email)
        self.assertRaises(Exception, self.db.update_email, 2, "new_email")

    def test_update_auth_key(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.update_auth_key(id, "new_auth_key")
        user = self.db.get_user(id)
        self.assertEqual(user["auth_key"], "new_auth_key")
        self.assertNotEqual(user["auth_key"], self.user_auth_key)
        self.assertRaises(
            Exception, self.db.update_auth_key, 2, "new_auth_key"
        )

    def test_get_id(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.assertIsNotNone(id)
        self.assertRaises(Exception, self.db.get_id, "test_user_2")

    def test_get_auth_key(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        auth_key = self.db.get_auth_key(id)
        self.assertEqual(auth_key, self.user_auth_key)
        self.assertRaises(Exception, self.db.get_auth_key, 2)

    def test_add_vault(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.add_vault(id, "test_vault", "test_key", "test_data")
        vault = self.db.get_vault(id, "test_vault")
        self.assertIsNotNone(vault)
        self.assertEqual(vault["name"], "test_vault")
        self.assertRaises(
            Exception, self.db.add_vault, id, "test_vault"
        )

    def test_delete_vault(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.add_vault(id, "test_vault", "test_key", "test_data")
        self.db.delete_vault(id, "test_vault")
        self.assertRaises(Exception, self.db.get_vault, id, "test_vault")

    def test_get_vault(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.add_vault(id, "test_vault", "test_key", "test_data")
        vault = self.db.get_vault(id, "test_vault")
        self.assertIsNotNone(vault)
        self.assertEqual(vault["name"], "test_vault")
        self.assertRaises(Exception, self.db.get_vault, id, "test_vault_2")

    def test_get_vault_key(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.add_vault(id, "test_vault", "test_key", "test_data")
        key = self.db.get_vault_key(id, "test_vault")
        self.assertEqual(key, "test_key")
        self.assertRaises(Exception, self.db.get_vault_key, id, "test_vault_2")

    def test_get_vault_data(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.add_vault(id, "test_vault", "test_key", "test_data")
        data = self.db.get_vault_data(id, "test_vault")
        self.assertEqual(data, "test_data")
        self.assertRaises(
            Exception, self.db.get_vault_data, id, "test_vault_2"
        )

    def test_get_vault_id(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.add_vault(id, "test_vault", "test_key", "test_data")
        vault_id = self.db.get_vault_id(id, "test_vault")
        self.assertIsNotNone(vault_id)
        self.assertRaises(
            Exception, self.db.get_vault_id, id, "test_vault_2"
        )

    def test_update_vault_name(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.add_vault(id, "test_vault", "test_key", "test_data")
        self.db.update_vault_name(id, "test_vault", "new_vault")
        vault = self.db.get_vault(id, "new_vault")
        self.assertIsNotNone(vault)
        self.assertEqual(vault["name"], "new_vault")
        self.assertRaises(
            Exception, self.db.update_vault_name, id,
            "test_vault_2", "new_vault"
        )

    def test_update_vault_key(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.add_vault(id, "test_vault", "test_key", "test_data")
        self.db.update_vault_key(id, "test_vault", "new_key")
        vault = self.db.get_vault(id, "test_vault")
        self.assertEqual(vault["key"], "new_key")
        self.assertNotEqual(vault["key"], "test_key")
        self.assertRaises(
            Exception, self.db.update_vault_key, id, "test_vault_2", "new_key"
        )

    def test_update_vault(self):
        self.db.add_user(self.user_email, self.user_auth_key)
        id = self.db.get_id(self.user_email)
        self.db.add_vault(id, "test_vault", "test_key", "test_data")
        self.db.update_vault(id, "test_vault", "new_data")
        vault = self.db.get_vault(id, "test_vault")
        self.assertEqual(vault["data"], "new_data")
        self.assertRaises(
            Exception, self.db.update_vault, id, "test_vault_2", "new_data"
        )
