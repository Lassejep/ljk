#!/usr/bin/env python3
import getpass
import sys
import pickle
import os
from random import choice
from websockets.sync.client import connect
from string import ascii_letters, digits, punctuation
from src import encryption, db


def generate_password(password_length=16):
    password = ''.join(
        choice(ascii_letters + digits + punctuation)
        for _ in range(password_length)
    )
    return password


def register(websocket):
    email = input("Enter your email: ")
    master_password = getpass.getpass("Enter a master password: ")
    repeat_password = getpass.getpass("Repeat your master password: ")
    if master_password != repeat_password:
        print("Passwords do not match, please try again")
        register(websocket)

    vault_name = input("Enter a name for your vault: ")
    command = "register"
    auth_key = encryption.hash_password(master_password)
    salt = encryption.generate_salt()
    master_key = encryption.generate_key(master_password, salt)
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
        print("Registration successful")
    else:
        print("Registration failed, please try again")
        register(websocket)


# TODO: Implement a better way to handle password authentication
def auth(websocket):
    email = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")
    msg = pickle.dumps({
        "command": "auth",
        "email": email,
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    auth_key = response["auth_key"]
    if not encryption.checkpw(password.encode(), auth_key):
        print("Login failed, please try again")
        auth(websocket)
    msg = websocket.send("verified")
    print("Login successful")

    user = pickle.loads(websocket.recv())
    print(f"Welcome {user['email']}")
    return user, password


def get_vaults(websocket, uid):
    msg = pickle.dumps({
        "command": "get_vaults",
        "uid": uid
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    vaults = response["vaults"]
    return vaults


def get_vault(websocket, user, vault_name, master_password):
    msg = pickle.dumps({
        "command": "get_vault",
        "uid": user["id"],
        "vault_name": vault_name
    })
    websocket.send(msg)
    response = pickle.loads(websocket.recv())
    encrypted_vault_key = response["key"]
    master_key = encryption.generate_key(master_password, user["salt"])
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
        print("Vault saved")
    else:
        print("Vault not saved")


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
                password = generate_password()
                notes = input("Enter any notes: ")
                vault.add_service(service, username, password, notes)
                vault.commit()
                print("Entry added to vault")
            case "get":
                service_id = command[1]
                entry = vault.find_service(service_id)
                if entry:
                    print("---------------------------")
                    print(f"ID: {entry['service_id']}")
                    print(f"Service: {entry['service']}")
                    print(f"Username: {entry['username']}")
                    print(f"Password: {entry['password']}")
                    print(f"Notes: {entry['notes']}")
                    print("---------------------------\n")
                else:
                    print("Entry not found")
            case "delete":
                service_id = command[1]
                confirmation = input(
                    f"Are you sure you want to delete {service}? (y/n): "
                )
                if confirmation == "y":
                    vault.delete_service(service_id)
                    print("Entry deleted")
                else:
                    print("Entry not deleted")
            case "list":
                entries = vault.get_services()
                if not entries:
                    print("No entries in vault")
                    continue
                for entry in entries:
                    print("---------------------------")
                    print(f"ID: {entry['service_id']}")
                    print(f"Service: {entry['service']}")
                    print(f"Username: {entry['username']}")
                    print(f"Password: {entry['password']}")
                    print(f"Notes: {entry['notes']}")
                print("---------------------------\n")
            case "search":
                service = command[1]
                entries = vault.search_services(service)
                if not entries:
                    print("No services match your search")
                    continue
                for entry in entries:
                    print("---------------------------")
                    print(f"ID: {entry['service_id']}")
                    print(f"Service: {entry['service']}")
                    print(f"Username: {entry['username']}")
                    print(f"Password: {entry['password']}")
                    print(f"Notes: {entry['notes']}")
                print("---------------------------\n")
            case "clear":
                os.system("clear")
            case "exit":
                print("Goodbye")
                vault.commit()
                break
            case _:
                print("Invalid command, type 'help' for a list of commands")


if __name__ == "__main__":
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    if len(sys.argv) != 2:
        print("Usage: ./ljkey.py [register/auth]")
        sys.exit(1)

    with connect("ws://localhost:8765") as websocket:
        if sys.argv[1] == "register":
            register(websocket)
            user, master_pass = auth(websocket)
        elif sys.argv[1] == "auth":
            user, master_pass = auth(websocket)
        else:
            print("Usage: ./ljkey.py [register/auth]")
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
        save_vault(websocket, user, vault, vault_key)
        os.remove(f"tmp/vault_{vault_name}.db")
