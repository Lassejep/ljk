from . import encryption
import pyperclip


def help():
    print("Commands:")
    print("add <service>: Add an entry to the vault")
    print("get <service_id>: Get an entry from the vault")
    print("delete <service_id>: Delete an entry from the vault")
    print("search <query>: Search for a service in the vault")
    print("list: List all entries in the vault")
    print("clear: Clear the terminal screen")
    print("exit: Exit the program")
    print("help: Display this help message")


def add_service(service, vault):
    username = input("Enter the username: ")
    generate_password = input("Generate a password? (Y/n): ").lower()
    if generate_password == "n" or generate_password == "no":
        password = input("Enter the password: ")
    else:
        password = encryption.generate_password()
    notes = input("Enter any notes: ")
    vault.add(service, username, password, notes)
    vault.commit()
    print("Entry added to vault")


def get_service(service_id, vault):
    entry = vault.service(service_id)
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


def delete_service(service_id, vault):
    service = vault.service(service_id)
    confirmation = input(
        f"Are you sure you want to delete {service['service']}? (y/N): "
    ).lower()
    if confirmation == "y" or confirmation == "yes":
        vault.delete(service_id)
        vault.commit()
        print("Entry deleted")
    else:
        print("Entry not deleted")


def search_service(query, vault):
    entries = vault.search(query)
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


def list_services(vault):
    entries = vault.services()
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

# TODO: Account auth and registration
# TODO: Account Master Password change
# TODO: Vault changes, creation, and deletion
# TODO: Service modification
