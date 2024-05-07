import unittest
import os
from src import db, encryption, handlers
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
        self.vault_key = encryption.generate_vault_key()
        self.vault = db.Vault(self.vault_name, self.vault_key)
        self.vault_path = f"tmp/vault_{self.vault_name}.db"
        self.service = "test_service"
        self.user = "test_user"
        self.password = "test_password"
        self.notes = "test_notes"

    def test_register(self):
        response = handlers.register(
            self.ws, self.email, self.master_pass, self.vault
        )
        self.assertEqual(response, True)

    def test_login(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        self.assertIsNotNone(user)

    def test_get_vaults(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        vaults = handlers.get_vaults(self.ws, user["id"])
        self.assertEqual(len(vaults), 1)
        self.assertEqual(vaults[0], self.vault_name)

    def test_get_vault(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault
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
            self.ws, self.email, self.master_pass, self.vault
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        handlers.get_vault(
            self.ws, user, self.vault_name, self.master_pass
        )
        self.vault.add(self.service, self.user, self.password, self.notes)
        save = handlers.save_vault(self.ws, user, self.vault)
        self.assertTrue(save)

    def test_create_vault(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        new_vault_name = "new_vault"
        new_vault_key = encryption.generate_vault_key()
        new_vault = db.Vault(new_vault_name, new_vault_key)
        handlers.create_vault(self.ws, user, new_vault, self.master_pass)
        vaults = handlers.get_vaults(self.ws, user["id"])
        self.assertEqual(len(vaults), 2)
        self.assertNotEqual(vaults[0], new_vault_name)
        self.assertEqual(vaults[1], new_vault_name)

    def test_delete_vault(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        handlers.delete_vault(self.ws, user, self.vault_name)
        vaults = handlers.get_vaults(self.ws, user["id"])
        self.assertEqual(len(vaults), 0)

    def test_change_master_pass(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        new_master_pass = "new_master_pass"
        self.vault.add(self.service, self.user, self.password, self.notes)
        status = handlers.change_master_pass(
            self.ws, user, self.master_pass, new_master_pass
        )
        self.assertTrue(status)
        user = handlers.auth(self.ws, self.email, new_master_pass)
        self.assertIsNotNone(user)

    def test_change_email(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        new_email = "new_email"
        status = handlers.change_email(self.ws, user, new_email)
        self.assertTrue(status)
        user = handlers.auth(self.ws, new_email, self.master_pass)
        self.assertIsNotNone(user)

    def test_delete_account(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        handlers.delete_account(self.ws, user)
        user = handlers.auth(self.ws, self.email, self.master_pass)
        self.assertIsNone(user)

    def test_update_vault_key(self):
        handlers.register(
            self.ws, self.email, self.master_pass, self.vault
        )
        user = handlers.auth(self.ws, self.email, self.master_pass)
        new_vault_key = encryption.generate_vault_key()
        status = handlers.update_vault_key(
            self.ws, user, self.vault_name, new_vault_key
        )
        self.assertTrue(status)

    def tearDown(self):
        self.vault.rm()
        self.ws.close()
        os.remove(self.db_path)
