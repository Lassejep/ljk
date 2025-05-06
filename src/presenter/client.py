import pickle
from src.model import encryption
from src.model.vault import Vault


async def register(websocket, email, mpass):
    command = "register"
    dkey = encryption.create_dkey(mpass, email)
    mkey = encryption.create_mkey(mpass, dkey)
    user = {"email": email, "mkey": mkey}
    msg = pickle.dumps({"command": command, "user": user})
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def auth(websocket, email, mpass):
    dkey = encryption.create_dkey(mpass, email)
    mkey = encryption.create_mkey(mpass, dkey)
    msg = pickle.dumps({"command": "auth", "email": email, "mkey": mkey})
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        user = response["user"]
        user["dkey"] = dkey
        return user
    else:
        return None


async def delete_account(websocket, user, mpass):
    command = "delete_account"
    uid = user["id"]
    mkey = encryption.create_mkey(mpass, user["dkey"])
    msg = pickle.dumps({"command": command, "uid": uid, "mkey": mkey})
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def change_mkey(websocket, user, mpass, new_mpass):
    if await auth(websocket, user["email"], mpass) is None:
        return False
    vaults = await get_vaults(websocket, user)
    new_dkey = encryption.create_dkey(new_mpass, user["email"])
    new_mkey = encryption.create_mkey(new_mpass, new_dkey)
    if vaults is not None:
        for vault in vaults:
            vault_name = vault["name"]
            e_vkey = vault["key"]
            vkey = encryption.decrypt(e_vkey, user["dkey"])
            new_e_vkey = encryption.encrypt(vkey, new_dkey)
            if not await update_vault_key(
                websocket, user, vault_name, new_e_vkey
            ):
                return False
    msg = pickle.dumps({
        "command": "change_auth_key", "uid": user["id"], "new_mkey": new_mkey
    })
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def change_email(websocket, user, new_email, mpass):
    if await auth(websocket, user["email"], mpass) is None:
        return False
    new_dkey = encryption.create_dkey(mpass, new_email)
    new_mkey = encryption.create_mkey(mpass, new_dkey)
    vaults = await get_vaults(websocket, user)
    if vaults is not None:
        for vault in vaults:
            vault_name = vault["name"]
            e_vkey = vault["key"]
            vkey = encryption.decrypt(e_vkey, user["dkey"])
            e_vkey = encryption.encrypt(vkey, new_dkey)
            if not await update_vault_key(websocket, user, vault_name, e_vkey):
                return False
    msg = pickle.dumps({
        "command": "change_email", "uid": user["id"], "new_email": new_email,
        "new_mkey": new_mkey
    })
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def get_vaults(websocket, user):
    msg = pickle.dumps({"command": "get_vaults", "uid": user["id"]})
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "failed" or response["vaults"] is None:
        return None
    vaults = response["vaults"]
    return vaults


async def get_vault(websocket, user, vault_name):
    msg = pickle.dumps({
        "command": "get_vault", "uid": user["id"], "vault_name": vault_name
    })
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "failed":
        return None
    vault = response["vault"]
    vkey = encryption.decrypt(vault["key"], user["dkey"])
    data = encryption.decrypt(vault["data"], vkey)
    vault = Vault(vault_name, vkey)
    vault.load(data)
    return vault


async def save_vault(websocket, user, vault):
    vault_data = vault.dump()
    e_vault = encryption.encrypt(vault_data, vault.key)
    msg = pickle.dumps({
        "command": "save_vault",
        "uid": user["id"],
        "vault_name": vault.name,
        "data": e_vault
    })
    vault.load(vault_data)
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def update_vault_key(websocket, user, vault_name, e_vkey):
    msg = pickle.dumps({
        "command": "update_vault_key",
        "uid": user["id"],
        "vault_name": vault_name,
        "vault_key": e_vkey
    })
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def update_vault_name(websocket, user, vault_name, new_vault_name):
    msg = pickle.dumps({
        "command": "update_vault_name",
        "uid": user["id"],
        "vault_name": vault_name,
        "new_vault_name": new_vault_name
    })
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def delete_vault(websocket, user, vault_name):
    msg = pickle.dumps({
        "command": "delete_vault",
        "uid": user["id"],
        "vault_name": vault_name
    })
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def create_vault(websocket, user, vault_name):
    vkey = encryption.generate_vault_key()
    vault = Vault(vault_name, vkey)
    e_vkey = encryption.encrypt(vkey, user["dkey"])
    e_vault = encryption.encrypt(vault.dump(), vkey)
    msg = pickle.dumps({
        "command": "create_vault",
        "uid": user["id"],
        "vault_name": vault_name,
        "vault_key": e_vkey,
        "vault_data": e_vault
    })
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False
