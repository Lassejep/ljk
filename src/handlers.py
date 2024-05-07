import pickle
from . import encryption


def register(websocket, email, master_pass, vault):
    command = "register"
    auth_key = encryption.hash_password(master_pass)
    salt = encryption.generate_salt()
    data_key = encryption.create_data_key(master_pass, salt)
    encrypted_vault_key = encryption.encrypt(vault.key, data_key)
    encrypted_vault = encryption.encrypt_file(
        f"tmp/vault_{vault.name}.db", vault.key
    )

    msg = pickle.dumps({
        "command": command,
        "email": email,
        "auth_key": auth_key,
        "salt": salt,
        "vault_name": vault.name,
        "vault_key": encrypted_vault_key,
        "vault_data": encrypted_vault
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


# TODO: Implement a better way to handle password authentication
def auth(websocket, email, master_pass):
    msg = pickle.dumps({
        "command": "auth",
        "email": email,
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "failed":
        msg = websocket.send("not_found")
        return None
    auth_key = response["auth_key"]
    if not encryption.verify_password(master_pass, auth_key):
        msg = websocket.send("unverified")
        return None
    msg = websocket.send("verified")
    user = pickle.loads(websocket.recv())
    return user


def delete_account(websocket, user):
    msg = pickle.dumps({
        "command": "delete_account",
        "email": user["email"]
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def change_master_pass(websocket, user, master_pass, new_master_pass):
    vaults = get_vaults(websocket, user["id"])
    for vault_name in vaults:
        vault_key = get_vault(websocket, user, vault_name, master_pass)
        new_data_key = encryption.create_data_key(
            new_master_pass, user["salt"]
        )
        encrypted_vault_key = encryption.encrypt(vault_key, new_data_key)
        if not update_vault_key(
            websocket, user, vault_name,
            encrypted_vault_key
        ):
            return False
    auth_key = encryption.hash_password(new_master_pass)
    msg = pickle.dumps({
        "command": "change_auth_key",
        "email": user["email"],
        "auth_key": auth_key
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def change_email(websocket, user, new_email):
    msg = pickle.dumps({
        "command": "change_email",
        "email": user["email"],
        "new_email": new_email
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def get_vaults(websocket, uid):
    msg = pickle.dumps({
        "command": "get_vaults",
        "uid": uid
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    vaults = response["vaults"]
    return vaults


def get_vault(websocket, user, vault_name, master_pass):
    msg = pickle.dumps({
        "command": "get_vault",
        "uid": user["id"],
        "vault_name": vault_name
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    encrypted_vault_key = response["key"]
    data_key = encryption.create_data_key(master_pass, user["salt"])
    vault_key = encryption.decrypt(
        encrypted_vault_key, data_key
    )
    encrypted_vault = response["data"]
    with open(f"tmp/vault_{vault_name}.db", "wb") as f:
        f.write(encrypted_vault)
    encryption.decrypt_file(f"tmp/vault_{vault_name}.db", vault_key)
    return vault_key


def save_vault(websocket, user, vault):
    encrypted_vault = encryption.encrypt_file(
        f"tmp/vault_{vault.name}.db", vault.key
    )
    msg = pickle.dumps({
        "command": "save_vault",
        "uid": user["id"],
        "vault_name": vault.name,
        "data": encrypted_vault
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False


def update_vault_key(websocket, user, vault_name, encrypted_vault_key):
    msg = pickle.dumps({
        "command": "update_vault_key",
        "uid": user["id"],
        "vault_name": vault_name,
        "vault_key": encrypted_vault_key
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


def create_vault(websocket, user, vault, master_pass):
    data_key = encryption.create_data_key(master_pass, user["salt"])
    encrypted_vault_key = encryption.encrypt(vault.key, data_key)
    encrypted_vault = encryption.encrypt_file(
        f"tmp/vault_{vault.name}.db", vault.key
    )
    msg = pickle.dumps({
        "command": "create_vault",
        "uid": user["id"],
        "vault_name": vault.name,
        "vault_key": encrypted_vault_key,
        "vault_data": encrypted_vault
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    if response["status"] == "success":
        return True
    else:
        return False
