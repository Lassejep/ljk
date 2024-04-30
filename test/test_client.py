import unittest
import os
import ljkey
from src import db
from websockets.sync.client import connect


class TestClient(unittest.TestCase):
    def setUp(self):
        self.db_path = "/tmp/test.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.ws = connect("ws://localhost:8765")
        self.test_email = "test_email"
        self.test_master_password = "test_master_password"
        self.test_vault_path = "tmp/vault_test_vault.db"
        self.test_vault = "test_vault"
        self.test_service = "test_service"
        self.test_user = "test_user"
        self.test_password = "test_password"
        self.test_notes = "test_notes"

    def test_register(self):
        response = ljkey.register(
            self.ws,
            self.test_email,
            self.test_master_password,
            self.test_vault
        )
        self.assertEqual(response, True)

    def test_login(self):
        ljkey.register(
            self.ws,
            self.test_email,
            self.test_master_password,
            self.test_vault
        )

        user = ljkey.auth(
            self.ws,
            self.test_email,
            self.test_master_password,
        )
        self.assertIsNotNone(user)

    def test_get_vaults(self):
        ljkey.register(
            self.ws,
            self.test_email,
            self.test_master_password,
            self.test_vault
        )

        user = ljkey.auth(
            self.ws, self.test_email, self.test_master_password,
        )

        vaults = ljkey.get_vaults(self.ws, user["id"])
        self.assertEqual(len(vaults), 1)
        self.assertEqual(vaults[0], self.test_vault)

    def test_get_vault(self):
        ljkey.register(
            self.ws,
            self.test_email,
            self.test_master_password,
            self.test_vault
        )

        user = ljkey.auth(
            self.ws, self.test_email, self.test_master_password,
        )
        vault_key = ljkey.get_vault(
            self.ws, user, self.test_vault, self.test_master_password
        )
        self.assertIsNotNone(vault_key)
        self.assertTrue(os.path.exists(self.test_vault_path))

    def test_save_vault(self):
        ljkey.register(
            self.ws,
            self.test_email,
            self.test_master_password,
            self.test_vault
        )

        user = ljkey.auth(
            self.ws, self.test_email, self.test_master_password,
        )
        vault_key = ljkey.get_vault(
            self.ws, user, self.test_vault, self.test_master_password
        )

        vault = db.Vault(self.test_vault)
        vault.add(
            self.test_service, self.test_user, self.test_password, self.test_notes
        )
        save = ljkey.save_vault(
            self.ws, user, vault, vault_key
        )
        self.assertTrue(save)

    def tearDown(self):
        vault = db.Vault(self.test_vault)
        vault.rm()
        self.ws.close()
        os.remove(self.db_path)
