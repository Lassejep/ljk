import pickle
from . import encryption, db


def register(websocket, email, mkey):
    command = "register"
    auth_key = encryption.hash_password(mkey)
    salt = encryption.generate_salt()
    user = {"email": email, "salt": salt, "auth_key": auth_key}
    msg = pickle.dumps({"command": command, "user": user})
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def auth(websocket, email, mkey):
    msg = pickle.dumps({"command": "auth", "email": email, "mkey": mkey})
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return response["user"]
    else:
        return None


def delete_account(websocket, user):
    command = "delete_account"
    uid = user["id"]
    msg = pickle.dumps({"command": command, "uid": uid})
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def change_mkey(websocket, user, mkey, new_mkey):
    vaults = get_vaults(websocket, user)
    for vault in vaults:
        vault_name = vault["name"]
        dkey = encryption.create_data_key(new_mkey, user["salt"])
        vkey = get_vault(websocket, user, vault_name, mkey)
        e_vkey = encryption.encrypt(vkey, dkey)
        if not update_vault_key(websocket, user, vault_name, e_vkey):
            return False
    auth_key = encryption.hash_password(new_mkey)
    msg = pickle.dumps({
        "command": "change_auth_key", "uid": user["id"], "auth_key": auth_key
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def change_email(websocket, user, new_email):
    msg = pickle.dumps({
        "command": "change_email", "uid": user["id"], "new_email": new_email
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def get_vaults(websocket, user):
    msg = pickle.dumps({"command": "get_vaults", "uid": user["id"]})
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "failed":
        return None
    vaults = response["vaults"]
    return vaults


def get_vault(websocket, user, vault_name, mkey):
    msg = pickle.dumps({
        "command": "get_vault", "uid": user["id"], "vault_name": vault_name
    })
    websocket.send(msg)
    vault = pickle.loads(websocket.recv())
    dkey = encryption.create_data_key(mkey, user["salt"])
    vkey = encryption.decrypt(vault["key"], dkey)
    data = encryption.decrypt(vault["data"], vkey)
    vault = db.Vault(vault_name, vkey)
    vault.load(data)
    return vault


def save_vault(websocket, user, vault):
    e_vault = encryption.encrypt(vault.dump(), vault.key)
    msg = pickle.dumps({
        "command": "save_vault",
        "uid": user["id"],
        "vault_name": vault.name,
        "data": e_vault
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def update_vault_key(websocket, user, vault_name, e_vkey):
    msg = pickle.dumps({
        "command": "update_vault_key",
        "uid": user["id"],
        "vault_name": vault_name,
        "vault_key": e_vkey
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def delete_vault(websocket, user, vault_name):
    msg = pickle.dumps({
        "command": "delete_vault",
        "uid": user["id"],
        "vault_name": vault_name
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def create_vault(websocket, user, vault, mkey):
    dkey = encryption.create_data_key(mkey, user["salt"])
    e_vkey = encryption.encrypt(vault.key, dkey)
    e_vault = encryption.encrypt(vault.dump(), vault.key)
    msg = pickle.dumps({
        "command": "create_vault",
        "uid": user["id"],
        "vault_name": vault.name,
        "vault_key": e_vkey,
        "vault_data": e_vault
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False
