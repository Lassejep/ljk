import unittest
import os
from src import handlers
from src import db
from websockets.sync.client import connect


class TestClient(unittest.TestCase):
    def setUp(self):
        self.db_path = "/tmp/test.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.ws = connect("ws://localhost:8765")
        self.email = "email"
        self.master_pass = "master_pass"
        self.vault_name = "vault_name"
        self.vault = db.Vault(self.vault_name)
        self.vault_path = f"tmp/vault_{self.vault_name}.db"
        self.service = "test_service"
        self.user = "test_user"
        self.password = "test_password"
        self.notes = "test_notes"

    def test_register(self):
        response = handlers.register(
            self.ws, self.email, self.master_pass, self.vault_name
        )
        self.assertEqual(response, True)

    def test_login(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault_name
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        self.assertIsNotNone(user)

    def test_get_vaults(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault_name
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        vaults = handlers.get_vaults(self.ws, user["id"])
        self.assertEqual(len(vaults), 1)
        self.assertEqual(vaults[0], self.vault_name)

    def test_get_vault(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault_name
        )
        os.remove(self.vault_path)
        user = handlers.auth(self.ws, self.email, self.master_pass)
        vault_key = handlers.get_vault(
            self.ws, user, self.vault_name, self.master_pass
        )
        self.assertIsNotNone(vault_key)
        self.assertTrue(os.path.exists(self.vault_path))

    def test_save_vault(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault_name
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        vault_key = handlers.get_vault(
            self.ws, user, self.vault_name, self.master_pass
        )
        self.vault.add(self.service, self.user, self.password, self.notes)
        save = handlers.save_vault(self.ws, user, self.vault, vault_key)
        self.assertTrue(save)

    def tearDown(self):
        self.vault.rm()
        self.ws.close()
        os.remove(self.db_path)
