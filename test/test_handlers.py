import logging
import os
import pickle
import unittest
from typing import Any, Dict
from unittest.mock import AsyncMock

from websockets import ClientConnection

from src.model import db, handlers


class TestHandlers(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.db_path = "test.db"
        self.db = db.UserDatabase(self.db_path)
        logging.basicConfig(
            filename="test.log",
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.rhost = "test_host"
        self.rport = 1234

        self.ws = AsyncMock(spec=ClientConnection)

        async def send_side_effect(message: bytes) -> None:
            self.ws.message = message

        self.ws.send.side_effect = send_side_effect

        async def recv_side_effect() -> dict:
            return pickle.loads(self.ws.message)

        self.ws.recv.side_effect = recv_side_effect

    async def asyncTearDown(self) -> None:
        self.db.close()
        os.remove(self.db_path)

    async def test_register_user(self) -> None:
        message = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        await handlers.register_user(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "failed", response)

    async def test_auth(self) -> None:
        registration_msg = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, registration_msg, self.db, self.rhost, self.rport
        )

        message = {"email": "test_email", "mkey": "test_master_key"}
        await handlers.auth(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        message = {"email": "test_email", "mkey": "wrong_master_key"}
        await handlers.auth(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "failed", response)

    async def test_change_email(self) -> None:
        registration_msg = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, registration_msg, self.db, self.rhost, self.rport
        )

        message = {"uid": 1, "new_email": "new_email", "new_mkey": "new_master_key"}
        await handlers.change_email(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_change_auth_key(self) -> None:
        registration_msg = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, registration_msg, self.db, self.rhost, self.rport
        )

        message = {"uid": 1, "new_mkey": "new_master_key"}
        await handlers.change_auth_key(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_get_vaults(self) -> None:
        registration_msg = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, registration_msg, self.db, self.rhost, self.rport
        )

        message: Dict[str, Any] = {"uid": 1}
        await handlers.get_vaults(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["vaults"], None, response)
        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(self.ws, message, self.db, self.rhost, self.rport)
        message = {
            "uid": 1,
            "vault_name": "test_vault_2",
            "vault_key": "test_key_2",
            "vault_data": "test_data_2",
        }
        await handlers.create_vault(self.ws, message, self.db, self.rhost, self.rport)
        message = {"uid": 1}
        await handlers.get_vaults(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        self.assertEqual(len(response["vaults"]), 2, response)

    async def test_get_vault(self) -> None:
        registration_msg = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, registration_msg, self.db, self.rhost, self.rport
        )

        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(self.ws, message, self.db, self.rhost, self.rport)
        message = {"uid": 1, "vault_name": "test_vault"}
        await handlers.get_vault(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_create_vault(self) -> None:
        registration_msg = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, registration_msg, self.db, self.rhost, self.rport
        )

        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_update_vault_key(self) -> None:
        registration_msg = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, registration_msg, self.db, self.rhost, self.rport
        )

        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(self.ws, message, self.db, self.rhost, self.rport)
        message = {"uid": 1, "vault_name": "test_vault", "vault_key": "new_vault_key"}
        await handlers.update_vault_key(
            self.ws, message, self.db, self.rhost, self.rport
        )
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)

    async def test_delete_vault(self) -> None:
        registration_msg = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, registration_msg, self.db, self.rhost, self.rport
        )

        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(self.ws, message, self.db, self.rhost, self.rport)
        message = {"uid": 1, "vault_name": "test_vault"}
        await handlers.delete_vault(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        self.assertRaises(Exception, self.db.get_vault, 1, "test_vault")

    async def test_invalid_command(self) -> None:
        message = {"command": "invalid_command"}
        await handlers.invalid_command(self.ws, message, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "failed", response)

    async def test_save_vault(self) -> None:
        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(self.ws, message, self.db, self.rhost, self.rport)
        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "data": "test_data and more data",
        }
        await handlers.save_vault(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        vault = self.db.get_vault(1, "test_vault")
        self.assertIsNotNone(vault)
        self.assertEqual(vault["name"], "test_vault")
        self.assertEqual(vault["data"], "test_data and more data")

    async def test_delete_account(self) -> None:
        registration_msg = {"user": {"email": "test_email", "mkey": "test_master_key"}}
        await handlers.register_user(
            self.ws, registration_msg, self.db, self.rhost, self.rport
        )

        message = {"uid": 1, "mkey": "test_master_key"}
        await handlers.delete_account(self.ws, message, self.db, self.rhost, self.rport)
        response = await self.ws.recv()
        self.assertEqual(response["status"], "success", response)
        self.assertRaises(Exception, self.db.get_id, "test_email")

    async def test_update_vault_name(self) -> None:
        message = {
            "uid": 1,
            "vault_name": "test_vault",
            "vault_key": "test_key",
            "vault_data": "test_data",
        }
        await handlers.create_vault(self.ws, message, self.db, self.rhost, self.rport)
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
