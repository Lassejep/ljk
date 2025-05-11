import logging
import pickle
from typing import Dict

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from websockets import ServerConnection

from .db import Database


async def register_user(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    user = msg["user"]
    try:
        auth_key = PasswordHasher().hash(user["mkey"])
        database.add_user(user["email"], auth_key)
        uid = database.get_id(user["email"])
        logging.info(f"{rhost}:{rport} registered user:{uid}")
        database.commit()
        response = pickle.dumps({"status": "success"})
    except Exception as e:
        logging.error(f"Error: {e}\nRolling back users database")
        database.rollback()
        response = pickle.dumps({"status": "failed", "error": str(e)})
    await ws.send(response)


async def auth(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        uid = database.get_id(msg["email"])
        auth_key = database.get_auth_key(uid)
        if PasswordHasher().verify(auth_key, msg["mkey"]):
            user = database.get_user(uid)
            logging.info(f"{rhost}:{rport} authenticated user:{uid}")
            response = pickle.dumps({"status": "success", "user": user})
        else:
            raise VerifyMismatchError
    except VerifyMismatchError:
        logging.error(f"{rhost}:{rport} invalid password for user:{uid}")
        response = pickle.dumps({"status": "failed", "error": "Invalid password"})
    except Exception as e:
        logging.error(f"Error: {e}")
        response = pickle.dumps({"status": "failed", "error": str(e)})
    await ws.send(response)


async def change_email(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        new_auth_key = PasswordHasher().hash(msg["new_mkey"])
        database.update_email(msg["uid"], msg["new_email"], new_auth_key)
        database.commit()
        logging.info(f"{rhost}:{rport} changed email for user:{msg['uid']}")
        response = pickle.dumps({"status": "success"})
        await ws.send(response)
    except Exception as e:
        logging.error(f"Error: {e}\nRolling back database")
        database.rollback()
        response = pickle.dumps({"status": "failed", "error": str(e)})
        await ws.send(response)


async def change_auth_key(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        new_auth_key = PasswordHasher().hash(msg["new_mkey"])
        database.update_auth_key(msg["uid"], new_auth_key)
        database.commit()
        logging.info(f"{rhost}:{rport} changed auth key for user:{msg['uid']}")
        response = pickle.dumps({"status": "success"})
        await ws.send(response)
    except Exception as e:
        logging.error(f"Error: {e}\nRolling back database")
        database.rollback()
        response = pickle.dumps({"status": "failed", "error": str(e)})
        await ws.send(response)


async def get_vaults(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        vaults = database.get_vaults(msg["uid"])
        response = pickle.dumps({"status": "success", "vaults": vaults})
        logging.info(f"{rhost}:{rport} received vaults for user:{msg['uid']}")
    except Exception as e:
        logging.error(f"Error: {e}")
        response = pickle.dumps({"status": "failed", "error": str(e)})
    await ws.send(response)


async def get_vault(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        vault = database.get_vault(msg["uid"], msg["vault_name"])
        response = pickle.dumps({"status": "success", "vault": vault})
        await ws.send(response)
        logging.info(f"{rhost}:{rport} received vault:{vault['id']}")
    except Exception as e:
        logging.error(f"Error: {e}")
        response = pickle.dumps({"status": "failed", "error": str(e)})
        await ws.send(response)
        await ws.close()


async def create_vault(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        database.add_vault(
            msg["uid"], msg["vault_name"], msg["vault_key"], msg["vault_data"]
        )
        vault_id = database.get_vault_id(msg["uid"], msg["vault_name"])
        logging.info(f"{rhost}:{rport} created vault:{vault_id}")
        database.commit()
        response = pickle.dumps({"status": "success"})
        await ws.send(response)
    except Exception as e:
        logging.error(f"Error: {e}\nRolling back database")
        database.rollback()
        response = pickle.dumps({"status": "failed", "error": str(e)})
        await ws.send(response)


async def update_vault_key(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        database.update_vault_key(msg["uid"], msg["vault_name"], msg["vault_key"])
        database.commit()
        vault_id = database.get_vault_id(msg["uid"], msg["vault_name"])
        logging.info(f"{rhost}:{rport} updated vault key for vault:{vault_id}")
        response = pickle.dumps({"status": "success"})
        await ws.send(response)
    except Exception as e:
        logging.error(f"Error: {e}\nRolling back database")
        database.rollback()
        response = pickle.dumps({"status": "failed", "error": str(e)})
        await ws.send(response)


async def delete_vault(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        database.delete_vault(msg["uid"], msg["vault_name"])
        database.commit()
        logging.info(f"{rhost}:{rport} deleted vault:{msg['vault_name']}")
        response = pickle.dumps({"status": "success"})
        await ws.send(response)
    except Exception as e:
        logging.error(f"Error: {e}\nRolling back database")
        database.rollback()
        response = pickle.dumps({"status": "failed", "error": str(e)})
        await ws.send(response)


async def invalid_command(
    ws: ServerConnection, msg: Dict, rhost: str, rport: int
) -> None:
    logging.error(f"{rhost}:{rport} sent invalid command {msg['command']}")
    response = pickle.dumps(
        {
            "status": "failed",
            "error": f"{rhost}:{rport} sent invalid command {msg['command']}",
        }
    )
    await ws.send(response)
    await ws.close()


async def save_vault(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        database.update_vault(
            msg["uid"],
            msg["vault_name"],
            msg["data"],
        )
        database.commit()
        vault_id = database.get_vault_id(msg["uid"], msg["vault_name"])
        logging.info(f"{rhost}:{rport} saved vault:{vault_id}")
        response = pickle.dumps({"status": "success"})
        await ws.send(response)
    except Exception as e:
        logging.error(f"Error: {e}\nRolling back database")
        database.rollback()
        response = pickle.dumps({"status": "failed", "error": str(e)})
        await ws.send(response)


async def delete_account(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        if not PasswordHasher().verify(database.get_auth_key(msg["uid"]), msg["mkey"]):
            raise VerifyMismatchError
        database.delete_user(msg["uid"])
        database.commit()
        logging.info(f"{rhost}:{rport} deleted user:{msg['uid']}")
        response = pickle.dumps({"status": "success"})
        await ws.send(response)
    except VerifyMismatchError:
        logging.error(f"{rhost}:{rport} invalid password for user:{msg['uid']}")
        response = pickle.dumps({"status": "failed", "error": "Invalid password"})
        await ws.send(response)
    except Exception as e:
        logging.error(f"Error: {e}\nRolling back database")
        database.rollback()
        response = pickle.dumps({"status": "failed", "error": str(e)})
        await ws.send(response)


async def update_vault_name(
    ws: ServerConnection, msg: Dict, database: Database, rhost: str, rport: int
) -> None:
    try:
        database.update_vault_name(msg["uid"], msg["vault_name"], msg["new_vault_name"])
        database.commit()
        logging.info(f"{rhost}:{rport} changed vault name for user:{msg['uid']}")
        response = pickle.dumps({"status": "success"})
        await ws.send(response)
    except Exception as e:
        logging.error(f"Error: {e}\nRolling back database")
        database.rollback()
        response = pickle.dumps({"status": "failed", "error": str(e)})
        await ws.send(response)
