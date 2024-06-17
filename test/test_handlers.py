import unittest
import os
import logging
import pickle
from src import handlers, db


class TestHandlers(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_path = "test.db"
        self.db = db.Database(self.db_path)
        logging.basicConfig(
            filename="test.log",
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.rhost = "test_host"
        self.rport = "test_port"
        self.ws = MockServer()

    async def asyncTearDown(self):
        self.db.close()
        os.remove(self.db_path)

    async def test_register_user(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "failed", response)

    async def test_auth(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )

        message = {"email": "test_email", "mkey": "test_master_key"}
        await handlers.auth(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        message = {"email": "test_email", "mkey": "wrong_master_key"}
        await handlers.auth(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "failed", response)

    async def test_change_email(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )

        message = {
            "uid": 1, "new_email": "new_email", "new_mkey": "new_master_key"
        }
        await handlers.change_email(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_change_auth_key(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )

        message = {"uid": 1, "new_mkey": "new_master_key"}
        await handlers.change_auth_key(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_get_vaults(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )

        message = {"uid": 1}
        await handlers.get_vaults(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["vaults"], None, response)
        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        message = {
            "uid": 1,
            "vault_name": "test_vault_2",
            "vault_key": "test_key_2",
            "vault_data": "test_data_2",
        }
        await handlers.create_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        message = {"uid": 1}
        await handlers.get_vaults(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        self.assertEqual(len(response["vaults"]), 2, response)

    async def test_get_vault(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )

        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        message = {"uid": 1, "vault_name": "test_vault"}
        await handlers.get_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_create_vault(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )

        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_update_vault_key(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )

        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        message = {
            "uid": 1, "vault_name": "test_vault", "vault_key": "new_vault_key"
        }
        await handlers.update_vault_key(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_delete_vault(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )

        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        message = {"uid": 1, "vault_name": "test_vault"}
        await handlers.delete_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        self.assertRaises(Exception, self.db.get_vault, 1, "test_vault")

    async def test_invalid_command(self):
        message = {"command": "invalid_command"}
        await handlers.invalid_command(
            self.ws, message, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "failed", response)

    async def test_save_vault(self):
        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "data": "test_data and more data",
        }
        await handlers.save_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        vault = self.db.get_vault(1, "test_vault")
        self.assertIsNotNone(vault)
        self.assertEqual(vault["name"], "test_vault")
        self.assertEqual(vault["data"], "test_data and more data")

    async def test_delete_account(self):
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, message, self.db, self.rhost, self.rport
        )

        message = {"uid": 1, "mkey": "test_master_key"}
        await handlers.delete_account(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        self.assertRaises(Exception, self.db.get_id, "test_email")

    async def test_update_vault_name(self):
        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(
            self.ws, message, self.db, self.rhost, self.rport
        )
        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "new_vault_name": "new_vault",
        }
        await handlers.update_vault_name(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        self.assertRaises(Exception, self.db.get_vault, 1, "test_vault")


class MockServer():
    def __init__(self):
        self.message = None

    async def send(self, message):
        self.message = message

    async def recv(self):
        return pickle.loads(self.message)

    async def close(self):
        del self
