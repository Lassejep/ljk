import unittest
import os
import websockets
import ssl
from src import encryption, handlers


class TestClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_path = "/tmp/test.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        localhost_pem = "/home/tinspring/ws/ljk/localhost.pem"
        ssl_context.load_verify_locations(localhost_pem)
        self.ws = await websockets.connect(
            "wss://localhost:8765", ssl=ssl_context, ping_interval=None
        )
        self.email = "email"
        self.mkey = "mkey"
        self.vault_name = "vault_name"
        self.vkey = encryption.generate_vault_key()
        self.vault = None
        self.service = "test_service"
        self.user = "test_user"
        self.password = "test_password"
        self.notes = "test_notes"

    async def test_register(self):
        response = await handlers.register(self.ws, self.email, self.mkey)
        self.assertEqual(response, True)

    async def test_login(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        self.assertIsNotNone(user)

    async def test_get_vaults(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        await handlers.create_vault(self.ws, user, self.vault_name, self.mkey)
        vaults = await handlers.get_vaults(self.ws, user)
        self.assertEqual(len(vaults), 1)
        self.assertEqual(vaults[0]["name"], self.vault_name)

    async def test_get_vault(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        await handlers.create_vault(self.ws, user, self.vault_name, self.mkey)
        vault = await handlers.get_vault(
            self.ws, user, self.vault_name, self.mkey
        )
        self.assertIsNotNone(vault)
        self.assertIsNotNone(vault.connection)

    async def test_save_vault(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        await handlers.create_vault(self.ws, user, self.vault_name, self.mkey)
        self.vault = await handlers.get_vault(
            self.ws, user, self.vault_name, self.mkey
        )
        self.vault.add(self.service, self.user, self.password, self.notes)
        save = await handlers.save_vault(self.ws, user, self.vault)
        self.assertTrue(save)

    async def test_create_vault(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        await handlers.create_vault(self.ws, user, self.vault_name, self.mkey)
        new_vault_name = "new_vault"
        await handlers.create_vault(self.ws, user, new_vault_name, self.mkey)
        vaults = await handlers.get_vaults(self.ws, user)
        self.assertEqual(len(vaults), 2)
        self.assertNotEqual(vaults[0]["name"], new_vault_name)
        self.assertEqual(vaults[1]["name"], new_vault_name)

    async def test_delete_vault(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        await handlers.create_vault(self.ws, user, self.vault_name, self.mkey)
        vaults = await handlers.get_vaults(self.ws, user)
        self.assertTrue(len(vaults) > 0)
        await handlers.delete_vault(self.ws, user, self.vault_name)
        vaults = await handlers.get_vaults(self.ws, user)
        self.assertEqual(len(vaults), 0)

    async def test_change_master_pass(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        await handlers.create_vault(self.ws, user, self.vault_name, self.mkey)
        self.vault = await handlers.get_vault(
            self.ws, user, self.vault_name, self.mkey
        )
        new_mkey = "new_master_pass"
        self.vault.add(self.service, self.user, self.password, self.notes)
        status = await handlers.change_mkey(self.ws, user, self.mkey, new_mkey)
        self.assertTrue(status)
        user = await handlers.auth(self.ws, self.email, new_mkey)
        self.assertIsNotNone(user)

    async def test_change_email(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        new_email = "new_email"
        status = await handlers.change_email(self.ws, user, new_email)
        self.assertTrue(status)
        user = await handlers.auth(self.ws, new_email, self.mkey)
        self.assertIsNotNone(user)

    async def test_delete_account(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        await handlers.delete_account(self.ws, user)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        self.assertIsNone(user)

    async def test_update_vault_key(self):
        await handlers.register(self.ws, self.email, self.mkey)
        user = await handlers.auth(self.ws, self.email, self.mkey)
        await handlers.create_vault(self.ws, user, self.vault_name, self.mkey)
        new_vkey = encryption.generate_vault_key()
        status = await handlers.update_vault_key(
            self.ws, user, self.vault_name, new_vkey
        )
        self.assertTrue(status)

    async def asyncTearDown(self):
        await self.ws.close()
        if self.vault is not None:
            self.vault.rm()
