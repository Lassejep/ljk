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
        self.assertIsNotNone(id)
        user = self.db.get_user(id)
        self.assertEqual(user["email"], self.user_email)
        self.assertEqual(user["auth_key"], self.user_auth_key)
