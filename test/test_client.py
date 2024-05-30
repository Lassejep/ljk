import unittest
import os
import websockets
import logging
import asyncio
import server
from src import encryption, client


class TestClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_path = "test.db"
        logging.basicConfig(
            filename="test.log",
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.server = asyncio.create_task(server.main(db_path=self.db_path))
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.ws = await websockets.connect(
            "wss://localhost:8765", ssl=None, ping_interval=None
        )
        self.email = "test_email"
        self.mpass = "master_pass"
        self.vault_name = "vault_name"
        self.vkey = encryption.generate_vault_key()
        self.vault = None
        self.service = "test_service"
        self.user = "test_user"
        self.password = "test_password"
        self.notes = "test_notes"

    async def test_register(self):
        response = await client.register(self.ws, self.email, self.mpass)
        self.assertEqual(response, True)

    async def test_login(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        self.assertIsNotNone(user)

    async def test_get_vaults(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        await client.create_vault(self.ws, user, self.vault_name)
        vaults = await client.get_vaults(self.ws, user)
        self.assertEqual(len(vaults), 1)
        self.assertEqual(vaults[0]["name"], self.vault_name)

    async def test_get_vault(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        await client.create_vault(self.ws, user, self.vault_name)
        vault = await client.get_vault(
            self.ws, user, self.vault_name
        )
        self.assertIsNotNone(vault)
        self.assertIsNotNone(vault.connection)

    async def test_save_vault(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        await client.create_vault(self.ws, user, self.vault_name)
        self.vault = await client.get_vault(
            self.ws, user, self.vault_name
        )
        self.vault.add(self.service, self.user, self.password, self.notes)
        save = await client.save_vault(self.ws, user, self.vault)
        self.assertTrue(save)

    async def test_create_vault(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        await client.create_vault(self.ws, user, self.vault_name)
        new_vault_name = "new_vault"
        await client.create_vault(self.ws, user, new_vault_name)
        vaults = await client.get_vaults(self.ws, user)
        self.assertEqual(len(vaults), 2)
        self.assertNotEqual(vaults[0]["name"], new_vault_name)
        self.assertEqual(vaults[1]["name"], new_vault_name)

    async def test_delete_vault(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        await client.create_vault(self.ws, user, self.vault_name)
        vaults = await client.get_vaults(self.ws, user)
        self.assertTrue(len(vaults) > 0)
        await client.delete_vault(self.ws, user, self.vault_name)
        vaults = await client.get_vaults(self.ws, user)
        self.assertIsNone(vaults)

    async def test_change_master_pass(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        await client.create_vault(self.ws, user, self.vault_name)
        self.vault = await client.get_vault(
            self.ws, user, self.vault_name
        )
        new_mpass = "new_master_pass"
        self.vault.add(self.service, self.user, self.password, self.notes)
        status = await client.change_mkey(self.ws, user, self.mpass, new_mpass)
        self.assertTrue(status)
        user = await client.auth(self.ws, self.email, new_mpass)
        self.assertIsNotNone(user)
        vaults = await client.get_vaults(self.ws, user)
        self.assertIsNotNone(vaults)

    async def test_change_email(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        await client.create_vault(self.ws, user, self.vault_name)
        new_email = "new_email"
        status = await client.change_email(
            self.ws, user, new_email, self.mpass
        )
        self.assertTrue(status)
        user = await client.auth(self.ws, new_email, self.mpass)
        self.assertIsNotNone(user)
        vaults = await client.get_vaults(self.ws, user)
        self.assertIsNotNone(vaults)

    async def test_delete_account(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        await client.delete_account(self.ws, user, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        self.assertIsNone(user)

    async def test_update_vault_key(self):
        await client.register(self.ws, self.email, self.mpass)
        user = await client.auth(self.ws, self.email, self.mpass)
        await client.create_vault(self.ws, user, self.vault_name)
        new_vkey = encryption.generate_vault_key()
        status = await client.update_vault_key(
            self.ws, user, self.vault_name, new_vkey
        )
        self.assertTrue(status)

    async def asyncTearDown(self):
        self.server.cancel()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        await self.ws.close()
        if self.vault is not None:
            self.vault.rm()
