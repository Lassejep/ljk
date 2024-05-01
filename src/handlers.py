import pickle
from . import encryption


def register(websocket, email, master_pass, vault_name):
    command = "register"
    auth_key = encryption.hash_password(master_pass)
    salt = encryption.generate_salt()
    master_key = encryption.create_data_key(master_pass, salt)
    vault_key = encryption.generate_vault_key()
    encrypted_vault_key = encryption.encrypt(vault_key, master_key)
    encrypted_vault = encryption.encrypt_file(
        f"tmp/vault_{vault_name}.db", vault_key
    )

    msg = pickle.dumps({
        "command": command,
        "email": email,
        "auth_key": auth_key,
        "salt": salt,
        "vault_name": vault_name,
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
    auth_key = response["auth_key"]
    if not encryption.verify_password(master_pass, auth_key):
        return None
    msg = websocket.send("verified")
    user = pickle.loads(websocket.recv())
    return user


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
    master_key = encryption.create_data_key(master_pass, user["salt"])
    vault_key = encryption.decrypt(
        encrypted_vault_key, master_key
    )
    encrypted_vault = response["data"]
    with open(f"tmp/vault_{vault_name}.db", "wb") as f:
        f.write(encrypted_vault)
    encryption.decrypt_file(f"tmp/vault_{vault_name}.db", vault_key)
    return vault_key


def save_vault(websocket, user, vault, vault_key):
    encrypted_vault = encryption.encrypt_file(
        f"tmp/vault_{vault.name}.db", vault_key
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
