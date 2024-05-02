import pyperclip
import getpass
import os
from . import encryption, db, handlers


class Console:
    def __init__(self, ws):
        self.ws = ws
        self.email = None
        self.master_pass = None
        self.user = None
        self.vault = None

    def run(self):
        while True:
            command = input("ljkey> ").split(" ", 2)
            if command[0] == "account":
                if len(command) < 2:
                    self.account_info()
                    continue
                match command[1]:
                    case "help":
                        self.account_help()
                    case "register":
                        self.account_register()
                    case "auth":
                        self.account_auth()
                    case "logout":
                        self.account_logout()
                    case "delete":
                        self.delete_account()
                    case "change-master-pass":
                        self.account_change_master_pass()
                    case "change-email":
                        self.account_change_email()
                    case _:
                        print("Invalid command")
                        self.account_help()
            elif command[0] == "vault":
                if self.user is None:
                    print("You must be logged in to access vaults")
                    continue
                if len(command) < 2:
                    self.vault_info()
                    continue
                match command[1]:
                    case "help":
                        self.vault_help()
                    case "ls":
                        self.vault_list()
                    case "select":
                        self.vault_select(command[2])
                    case "create":
                        self.vault_create()
                    case "rename":
                        self.vault_rename()
                    case "delete":
                        self.vault_delete()
                    case _:
                        print("Invalid command")
                        self.vault_help()
            else:
                if command[0] == "service":
                    if len(command) < 2:
                        continue
                    if command[1] == "help":
                        self.service_help()
                        continue
                    command = command[1:]
                match command[0]:
                    case "help":
                        self.help()
                    case "ls":
                        self.service_list()
                    case "search":
                        self.service_search(command[1])
                    case "get":
                        self.service_get(command[1])
                    case "add":
                        self.service_add(command[1])
                    case "edit":
                        self.service_edit(command[1])
                    case "delete":
                        self.service_delete(command[1])
                    case "exit":
                        break
                    case "quit":
                        break
                    case "clear":
                        os.system("clear")
                    case _:
                        print("Invalid command")
                        self.help()
        self.exit()

    def help(self):
        print("General Commands:")
        print("help: Display this help message")
        print("clear: Clear the screen")
        print("exit: Exit the program\n")
        self.account_help()
        self.vault_help()
        self.service_help()

    def account_help(self):
        print("Account Commands:")
        print("account help: Display this help message")
        print("account register: Register a new account")
        print("account auth: Authenticate with an existing account")
        print("account logout: Log out of the current account")
        print("account delete: Delete your account")
        print("account change-master-pass: Change your master password\n")

    def vault_help(self):
        print("Vault Commands:")
        print("vault help: Display this help message")
        print("vault ls: List all vaults")
        print("vault select <vault>: Select a vault")
        print("vault create: Create a new vault")
        print("vault rename: Rename the current vault")
        print("vault delete: Delete the current vault")
        print("vault save: Save the current vault\n")

    def service_help(self):
        print("Service Commands:")
        print("service help: Display this help message")
        print("ls: List all services in the current vault")
        print("search <query>: Search for a service")
        print("get <service>: Get a service")
        print("add <service>: Add a new service")
        print("edit <service>: Edit a service")
        print("delete <service>: Delete a service\n")

    def exit(self):
        if self.vault is not None:
            print("Saving vault")
            self.vault.commit()
            handlers.save_vault(self.ws, self.user, self.vault)
            self.vault.rm()
        print("Goodbye")

    def service_add(self, service):
        if self.user is None:
            print("You must be logged in to add a service")
            return
        if self.vault is None:
            print("No vault selected")
            return
        username = input("Enter the username: ")
        generate_password = input("Generate a password? (Y/n): ").lower()
        if generate_password == "n" or generate_password == "no":
            password = input("Enter the password: ")
        else:
            password = encryption.generate_password()
        notes = input("Enter any notes: ")
        self.vault.add(service, username, password, notes)
        self.vault.commit()
        print("Entry added to vault")

    def service_get(self, service_id):
        if self.user is None:
            print("You must be logged in to get a service")
            return
        if self.vault is None:
            print("No vault selected")
            return
        entry = self.vault.service(service_id)
        if entry is None:
            print("Entry not found")
            return
        print("---------------------------")
        print(f"Service ID: {entry['id']}")
        print(f"Service: {entry['service']}")
        print(f"User: {entry['user']}")
        print(f"Password: {entry['password']}")
        print(f"Notes: {entry['notes']}")
        print("---------------------------")
        copy = input("Copy password to clipboard? (y/N): ").lower()
        if copy == "y" or copy == "yes":
            pyperclip.copy(entry["password"])
            print("Password copied to clipboard")

    def service_delete(self, service_id):
        if self.user is None:
            print("You must be logged in to delete a service")
            return
        if self.vault is None:
            print("No vault selected")
            return
        service = self.vault.service(service_id)
        confirmation = input(
            f"Are you sure you want to delete {service['service']}? (y/N): "
        ).lower()
        if confirmation != "y" or confirmation != "yes":
            print("Entry not deleted")
            return
        self.vault.delete(service_id)
        self.vault.commit()
        print("Entry deleted")

    def service_search(self, query):
        if self.user is None:
            print("You must be logged in to search for a service")
            return
        if self.vault is None:
            print("No vault selected")
            return
        entries = self.vault.search(query)
        if entries is None:
            print("No services match your search")
            return
        for entry in entries:
            print("---------------------------")
            print(f"Service ID: {entry['id']}")
            print(f"Service: {entry['service']}")
            print(f"User: {entry['user']}")
            print(f"Notes: {entry['notes']}")
        print("---------------------------")

    def service_list(self):
        if self.user is None:
            print("You must be logged in to list services")
            return
        if self.vault is None:
            print("No vault selected")
            return
        entries = self.vault.services()
        if entries is None:
            print("No entries in vault")
            return
        for entry in entries:
            print("---------------------------")
            print(f"Service ID: {entry['id']}")
            print(f"Service: {entry['service']}")
            print(f"User: {entry['user']}")
            print(f"Notes: {entry['notes']}")
        print("---------------------------")

    def service_edit(self, service_id):
        if self.user is None:
            print("You must be logged in to edit a service")
            return
        if self.vault is None:
            print("No vault selected")
            return
        entry = self.vault.service(service_id)
        if entry is None:
            print("Entry not found")
            return
        print("---------------------------")
        print(f"Service ID: {entry['id']}")
        print(f"Service: {entry['service']}")
        print(f"User: {entry['user']}")
        print(f"Password: {entry['password']}")
        print(f"Notes: {entry['notes']}")
        print("---------------------------")
        service = input(f"Enter the new service name ({entry['service']}): ")
        if service == "":
            service = entry["service"]
        username = input(f"Enter the new username ({entry['user']}): ")
        if username == "":
            username = entry["user"]
        generate_password = input("Generate a new password? (y/N): ").lower()
        if generate_password == "y" or generate_password == "yes":
            password = encryption.generate_password()
        else:
            password = input(f"Enter the new password ({entry['password']}): ")
            if password == "":
                password = entry["password"]
        notes = input(f"Enter the new notes ({entry['notes']}): ")
        if notes == "":
            notes = entry["notes"]
        self.vault.update(service_id, service, username, password, notes)
        self.vault.commit()
        print("Entry updated")

    # Vault commands
    def vault_list(self):
        vaults = handlers.get_vaults(self.ws, self.user["id"])
        print("Vaults:")
        for vault in vaults:
            print(vault)

    def vault_select(self, vault_name):
        handlers.get_vault(
            self.ws, self.user, vault_name, self.master_pass
        )
        self.vault = db.Vault(vault_name)

    def vault_create(self):
        vault_name = input("Enter the name of the new vault: ")
        db.Vault(vault_name)
        handlers.create_vault(self.ws, self.user, vault_name, self.master_pass)
        print("Vault created")
        handlers.get_vault(self.ws, self.user, vault_name, self.master_pass)
        self.vault = db.Vault(vault_name)
        print(f"Vault changed to {vault_name}")

    def vault_rename(self):
        self.select_vault()
        new_name = input("Enter the new name for the vault: ")
        if new_name == "":
            print("No name entered")
            return
        self.vault.name = new_name
        handlers.save_vault(self.ws, self.user, self.vault)
        print("Vault renamed")

    def vault_delete(self):
        self.select_vault()
        confirmation = input(
            f"Are you sure you want to delete {self.vault.name}? (y/N): "
        ).lower()
        if confirmation != "y" or confirmation != "yes":
            print("Vault not deleted")
            return
        handlers.delete_vault(self.ws, self.user, self.vault.name)
        print("Vault deleted")

    def vault_info(self):
        print(f"Vault: {self.vault.name}")

    # Account commands
    def account_register(self):
        if self.user is not None:
            print("You are already logged in")
            return
        self.email = input("Enter your email: ")
        self.master_pass = getpass.getpass("Enter your master password: ")
        confirm_pass = getpass.getpass("Confirm your master password: ")
        if self.master_pass != confirm_pass:
            print("Passwords do not match - try again")
            self.account_register()
        vault_name = input("Enter the name of your vault: ")
        db.Vault(vault_name)
        handlers.register(self.ws, self.email, self.master_pass, vault_name)
        print("Registration complete")
        self.user = handlers.auth(self.ws, self.email, self.master_pass)

    def account_auth(self):
        if self.user is not None:
            print("You are already logged in")
            return
        self.email = input("Enter your email: ")
        self.master_pass = getpass.getpass("Enter your master password: ")
        self.user = handlers.auth(self.ws, self.email, self.master_pass)
        if not self.user:
            print("Invalid email or master password")
            self.account_auth()

    def account_change_master_pass(self):
        if self.user is None:
            print("You must be logged in to change your master password")
            return
        old_pass = getpass.getpass("Enter your current master password: ")
        if old_pass != self.master_pass:
            print("Incorrect password - try again")
            self.account_change_master_pass()
        new_pass = getpass.getpass("Enter your new master password: ")
        confirm_pass = getpass.getpass("Confirm your new master password: ")
        if new_pass != confirm_pass:
            print("Passwords do not match - try again")
            self.account_change_master_pass()
        handlers.change_master_pass(self.ws, self.user, new_pass)
        self.master_pass = new_pass
        print("Master password changed")

    def account_change_email(self):
        if self.user is None:
            print("You must be logged in to change your email")
            return
        new_email = input("Enter your new email: ")
        handlers.change_email(self.ws, self.user, new_email)
        self.email = new_email
        print("Email changed")

    def account_delete(self):
        if self.user is None:
            print("You must be logged in to delete your account")
            return
        confirmation = input(
            "Are you sure you want to delete your account? (y/N): "
        ).lower()
        if confirmation != "y" or confirmation != "yes":
            print("Account not deleted")
            return
        handlers.delete_account(self.ws, self.user)
        print("Account deleted")

    def account_logout(self):
        if self.user is None:
            print("You are not logged in")
            return
        self.__init__(self.ws)
        print("Logged out")

    def account_info(self):
        if self.user is None:
            print("You are not logged in")
            return
        print(f"Email: {self.user['email']}")
