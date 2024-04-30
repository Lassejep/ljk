#!/usr/bin/env python3
import getpass
import sys
import pickle
import os
from websockets.sync.client import connect
from src import encryption, db


def register(websocket, email, master_pass, vault_name):
    command = "register"
    auth_key = encryption.hash_password(master_pass)
    salt = encryption.generate_salt()
    master_key = encryption.generate_key(master_pass, salt)
    vault_key = encryption.generate_random_key()
    encrypted_vault_key = encryption.encrypt(master_key, vault_key)
    db.Vault(vault_name)
    encrypted_vault = encryption.encrypt_file(
        vault_key, f"tmp/vault_{vault_name}.db"
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
    if not encryption.checkpw(master_pass.encode(), auth_key):
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
    master_key = encryption.generate_key(master_pass, user["salt"])
    vault_key = encryption.decrypt(
        master_key, encrypted_vault_key
    )
    encrypted_vault = response["data"]
    with open(f"tmp/vault_{vault_name}.db", "wb") as f:
        f.write(encrypted_vault)
    encryption.decrypt_file(vault_key, f"tmp/vault_{vault_name}.db")
    return vault_key


def save_vault(websocket, user, vault, vault_key):
    encrypted_vault = encryption.encrypt_file(
        vault_key, f"tmp/vault_{vault.name}.db"
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


# TODO: Remove password from console and add copy to clipboard functionality
def vault_console(vault, vault_key):
    while True:
        command = input("ljkey> ").split(" ", 1)
        match command[0]:
            case "help":
                print("Commands:")
                print("add <service>: Add an entry to the vault")
                print("get <service_id>: Get an entry from the vault")
                print("delete <service_id>: Delete an entry from the vault")
                print("search <query>: Search for a service in the vault")
                print("list: List all entries in the vault")
                print("clear: Clear the terminal screen")
                print("exit: Exit the program")
                print("help: Display this help message")
            case "add":
                service = command[1]
                username = input("Enter the username: ")
                password = encryption.generate_password()
                notes = input("Enter any notes: ")
                vault.add(service, username, password, notes)
                vault.commit()
                print("Entry added to vault")
            case "get":
                service_id = command[1]
                entry = vault.service(service_id)
                if entry is None:
                    print("Entry not found")
                    continue
                print("---------------------------")
                print(f"Service ID: {entry['id']}")
                print(f"Service: {entry['service']}")
                print(f"User: {entry['user']}")
                print(f"Password: {entry['password']}")
                print(f"Notes: {entry['notes']}")
                print("---------------------------\n")
            case "delete":
                service_id = command[1]
                confirmation = input(
                    f"Are you sure you want to delete {service}? (y/n): "
                )
                if confirmation == "y":
                    vault.delete(service_id)
                    print("Entry deleted")
                else:
                    print("Entry not deleted")
            case "list":
                entries = vault.services()
                if entries is None:
                    print("No entries in vault")
                    continue
                for entry in entries:
                    print("---------------------------")
                    print(f"Service ID: {entry['id']}")
                    print(f"Service: {entry['service']}")
                    print(f"User: {entry['user']}")
                    print(f"Password: {entry['password']}")
                    print(f"Notes: {entry['notes']}")
                print("---------------------------\n")
            case "search":
                query = command[1]
                entries = vault.search(query)
                if entries is None:
                    print("No services match your search")
                    continue
                for entry in entries:
                    print("---------------------------")
                    print(f"Service ID: {entry['id']}")
                    print(f"Service: {entry['service']}")
                    print(f"User: {entry['user']}")
                    print(f"Password: {entry['password']}")
                    print(f"Notes: {entry['notes']}")
                print("---------------------------\n")
            case "clear":
                os.system("clear")
            case "exit":
                vault.commit()
                break
            case _:
                print("Invalid command, type 'help' for a list of commands")


if __name__ == "__main__":
    if not os.path.exists("tmp"):
        os.mkdir("tmp")

    with connect("ws://localhost:8765") as websocket:
        if len(sys.argv) > 1:
            if sys.argv[1] == "register":
                email = input("Enter your email: ")
                master_pass = getpass.getpass("Enter a master password: ")
                repeat_password = getpass.getpass(
                    "Repeat your master password: ")
                if master_pass != repeat_password:
                    print("Passwords do not match, please try again")
                    sys.exit(1)
                vault_name = input("Enter a name for your vault: ")
                register(websocket, email, master_pass, vault_name)
                print("Registration complete")

        print("Login")
        email = input("Enter your email: ")
        master_pass = getpass.getpass("Enter your password: ")
        user = auth(websocket, email, master_pass)
        if not user:
            print("Invalid email or password")
            sys.exit(1)

        vaults = get_vaults(websocket, user["id"])
        print("Vaults:")
        for i, vault in enumerate(vaults):
            print(f"{i + 1}. {vault}")
        vault_index = int(
            input("Enter the number of the vault you want to access: ")
        ) - 1
        vault_name = vaults[vault_index]
        vault_key = get_vault(websocket, user, vault_name, master_pass)
        vault = db.Vault(vault_name)
        print("Vault accessed")

        vault_console(vault, vault_key)
        save = save_vault(websocket, user, vault, vault_key)
        if save:
            print("Vault saved")
            vault.rm()
        else:
            print("Failed to save vault")
        print("Exiting program, goodbye")
