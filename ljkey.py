#!/usr/bin/env python3
import getpass
import sys
import os
from websockets.sync.client import connect
from src import db, handlers, console


# TODO: Remove password from console and add copy to clipboard functionality
def vault_console(vault, vault_key):
    while True:
        command = input("ljkey> ").split(" ", 1)
        match command[0]:
            case "help":
                console.help()
            case "add":
                console.add_service(command[1], vault)
            case "get":
                console.get_service(command[1], vault)
            case "delete":
                console.delete_service(command[1], vault)
            case "search":
                console.search_service(command[1], vault)
            case "list":
                console.list_services(vault)
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
                db.Vault(vault_name)
                handlers.register(websocket, email, master_pass, vault_name)
                print("Registration complete")

        print("Login")
        email = input("Enter your email: ")
        master_pass = getpass.getpass("Enter your password: ")
        user = handlers.auth(websocket, email, master_pass)
        if not user:
            print("Invalid email or password")
            sys.exit(1)

        vaults = handlers.get_vaults(websocket, user["id"])
        print("Vaults:")
        for i, vault in enumerate(vaults):
            print(f"{i + 1}. {vault}")
        vault_index = int(
            input("Enter the number of the vault you want to access: ")
        ) - 1
        vault_name = vaults[vault_index]
        vault_key = handlers.get_vault(
            websocket, user, vault_name, master_pass
        )
        vault = db.Vault(vault_name)
        print("Vault accessed")

        vault_console(vault, vault_key)
        save = handlers.save_vault(websocket, user, vault, vault_key)
        if save:
            print("Vault saved")
            vault.rm()
        else:
            print("Failed to save vault")
        print("Exiting program, goodbye")
