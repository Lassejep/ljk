import pickle
from . import encryption, vault


async def register(websocket, email, mkey):
    command = "register"
    auth_key = encryption.hash_password(mkey)
    salt = encryption.generate_salt()
    user = {"email": email, "salt": salt, "auth_key": auth_key}
    msg = pickle.dumps({"command": command, "user": user})
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def auth(websocket, email, mkey):
    msg = pickle.dumps({"command": "auth", "email": email, "mkey": mkey})
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return response["user"]
    else:
        return None


async def delete_account(websocket, user):
    command = "delete_account"
    uid = user["id"]
    msg = pickle.dumps({"command": command, "uid": uid})
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def change_mkey(websocket, user, mkey, new_mkey):
    vaults = await get_vaults(websocket, user)
    for vault in vaults:
        vault_name = vault["name"]
        e_vkey = vault["key"]
        dkey = encryption.create_data_key(mkey, user["salt"])
        vkey = encryption.decrypt(e_vkey, dkey)
        new_dkey = encryption.create_data_key(new_mkey, user["salt"])
        new_e_vkey = encryption.encrypt(vkey, new_dkey)
        if not await update_vault_key(websocket, user, vault_name, new_e_vkey):
            return False
    auth_key = encryption.hash_password(new_mkey)
    msg = pickle.dumps({
        "command": "change_auth_key", "uid": user["id"], "auth_key": auth_key
    })
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


async def change_email(websocket, user, new_email):
    msg = pickle.dumps({
        "command": "change_email", "uid": user["id"], "new_email": new_email
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
    if response["status"] == "failed":
        return None
    vaults = response["vaults"]
    return vaults


async def get_vault(websocket, user, vault_name, mkey):
    msg = pickle.dumps({
        "command": "get_vault", "uid": user["id"], "vault_name": vault_name
    })
    await websocket.send(msg)
    response = pickle.loads(await websocket.recv())
    if response["status"] == "failed":
        return None
    vault = response["vault"]
    dkey = encryption.create_data_key(mkey, user["salt"])
    vkey = encryption.decrypt(vault["key"], dkey)
    data = encryption.decrypt(vault["data"], vkey)
    vault = vault.Vault(vault_name, vkey)
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


async def create_vault(websocket, user, vault_name, mkey):
    vkey = encryption.generate_vault_key()
    vault = vault.Vault(vault_name, vkey)
    dkey = encryption.create_data_key(mkey, user["salt"])
    e_vkey = encryption.encrypt(vkey, dkey)
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
