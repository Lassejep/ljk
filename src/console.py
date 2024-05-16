import pyperclip
import getpass
import curses
import sys
from . import handlers
from .encryption import generate_password


class Console:
    def __init__(self, ws):
        self.ws = ws
        self.email = None
        self.mkey = None
        self.user = None
        self.vault = None

        self.screen = curses.initscr()
        self.screen_size = self.screen.getmaxyx()
        self.menu = curses.newwin(
            self.screen_size[0], int(self.screen_size[1] * 0.2), 0, 1
        )
        self.menu_size = self.menu.getmaxyx()
        self.menu_loc = self.menu.getbegyx()
        self.window = self.screen.subpad(
            self.screen_size[0] - 2, int(self.screen_size[1] * 0.8),
            0, int(self.screen_size[1] * 0.2)
        )
        self.window_size = self.window.getmaxyx()
        self.window_loc = self.window.getbegyx()
        self.widget = self.screen.subpad(
            int(self.window_size[0] * 0.8), int(self.window_size[1] * 0.6),
            self.window_loc[0] + int(self.window_size[0] * 0.1),
            self.window_loc[1] + int(self.window_size[1] * 0.2)
        )
        self.widget_size = self.widget.getmaxyx()
        self.widget_loc = self.widget.getbegyx()
        self.msgbox = self.screen.subpad(
            3, self.window_size[1],
            self.window_size[0] - 1, self.window_loc[1]
        )

        curses.start_color()
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        self.text_color = curses.color_pair(0)
        self.hl_color = curses.color_pair(2)
        self.error_color = curses.color_pair(4)

    async def run(self):
        try:
            await self.start_menu()
        except Exception as e:
            await self.exit(e)
        except KeyboardInterrupt:
            await self.exit()

    async def exit(self, error=None):
        if self.vault is not None:
            await self.message("Saving vault")
            self.vault.commit()
            await handlers.save_vault(self.ws, self.user, self.vault)
            self.vault.rm()
        await self.message("Exiting")
        curses.echo()
        curses.endwin()
        if error is not None:
            print(error)
        sys.exit()

    async def message(self, message, color=None):
        self.msgbox.erase()
        self.msgbox.box()
        if color is not None:
            self.msgbox.addstr(1, 1, message, color)
        else:
            self.msgbox.addstr(1, 1, message)
        self.msgbox.noutrefresh()
        curses.doupdate()

    async def wait_for_key(self):
        key = None
        while key != ord("q"):
            key = self.screen.getch()

    async def navigate(self, key, window, y, length):
        position = window.getyx()
        if key == "k" or key == "KEY_UP":
            position = (position[0] - 1, position[1])
        if key == "j" or key == "KEY_DOWN":
            position = (position[0] + 1, position[1])
        try:
            position = (int(key), position[1])
        except ValueError:
            pass
        if key == "h" or key == "KEY_LEFT":
            pass
        if key == "l" or key == "KEY_RIGHT":
            pass
        if position[0] < y:
            position = (y + length - 1, position[1])
        if position[0] > y + length - 1:
            position = (y, position[1])
        window.move(*position)
        return position

    # Menus
    async def start_menu(self):
        self.menu.keypad(True)
        curses.noecho()
        curses.curs_set(0)
        key = "1"
        while key != "\n":
            pos = await self.navigate(key, self.menu, y=1, length=3)
            self.menu.erase()
            self.menu.box()
            self.menu.addstr(0, 1, "Menu")
            self.menu.addstr(1, 1, "1. Login")
            self.menu.addstr(2, 1, "2. Register")
            self.menu.addstr(3, 1, "3. Exit")
            selected_string = self.menu.instr(
                pos[0], 1, self.menu.getmaxyx()[1] - 4
            ).decode("utf-8")
            self.menu.addstr(pos[0], 1, " " + selected_string, self.hl_color)
            key = self.menu.getkey()

        if pos[0] == 1:
            await self.account_auth()
        elif pos[0] == 2:
            await self.account_register()
        elif pos[0] == 3:
            await self.exit()

    async def main_menu(self):
        self.menu.keypad(True)
        curses.noecho()
        curses.curs_set(0)
        key = "1"
        while key != "\n":
            pos = await self.navigate(key, self.menu, y=1, length=5)
            self.menu.erase()
            self.menu.box()
            self.menu.addstr(0, 1, "Menu")
            self.menu.addstr(1, 1, "1. Services")
            self.menu.addstr(2, 1, "2. Vaults")
            self.menu.addstr(3, 1, "3. Settings")
            self.menu.addstr(4, 1, "4. Logout")
            self.menu.addstr(5, 1, "5. Exit")

            selected_string = self.menu.instr(
                pos[0], 1, self.menu.getmaxyx()[1] - 4
            ).decode("utf-8")
            self.menu.addstr(pos[0], 1, " " + selected_string, self.hl_color)

            key = self.menu.getkey()

        if pos[0] == 1:
            await self.services_menu()
        elif pos[0] == 2:
            await self.vaults_menu()
        elif pos[0] == 3:
            await self.settings_menu()
        elif pos[0] == 4:
            await self.account_logout()
        elif pos[0] == 5:
            await self.exit()

    # Start menu windows
    async def account_auth(self):
        self.window.erase()
        self.window.box()
        curses.echo()
        curses.curs_set(1)

        self.window.addstr(0, 1, "Login")
        email_field = "Enter your email: "
        password_field = "Enter your master password: "
        self.window.addstr(2, 1, email_field)
        self.window.addstr(3, 1, password_field)
        self.email = self.window.getstr(
            2, len(email_field) + 1
        ).decode("utf-8")
        curses.noecho()
        self.mkey = self.window.getstr(
            3, len(password_field) + 1
        ).decode("utf-8")
        self.user = await handlers.auth(self.ws, self.email, self.mkey)
        curses.echo()
        if self.user is None:
            await self.message("Failed to log in", self.error_color)
            return
        await self.message("Logged in")
        await self.main_menu()

    async def account_register(self):
        self.window.erase()
        self.window.box()
        curses.echo()
        curses.curs_set(1)

        email_field = "Enter your email: "
        password_field = "Enter your master password: "
        confirm_field = "Repeat your master password: "
        self.window.addstr(0, 1, "Register")
        self.window.addstr(1, 1, email_field)
        self.window.addstr(2, 1, password_field)
        self.window.addstr(3, 1, confirm_field)

        self.email = self.window.getstr(
            1, len(email_field) + 1
        ).decode("utf-8")
        curses.noecho()
        self.mkey = self.window.getstr(
            2, len(password_field) + 1
        ).decode("utf-8")
        confirm_pass = self.window.getstr(
            3, len(confirm_field) + 1
        ).decode("utf-8")
        if self.mkey != confirm_pass:
            await self.message("Passwords do not match", self.error_color)
            await self.account_register()
            return
        if not await handlers.register(self.ws, self.email, self.mkey):
            await self.message("Failed to register", self.error_color)
            await self.account_register()
            return
        await self.message("Registered")
        self.user = await handlers.auth(self.ws, self.email, self.mkey)
        if self.user is None:
            await self.message("Failed to log in", self.error_color)
            await self.account_auth()
            return
        await self.message("Logged in")
        await self.main_menu()

    # Main menu windows
    async def vaults_menu(self):
        self.window.keypad(True)
        curses.set_escdelay(25)
        curses.noecho()
        curses.curs_set(0)

        key = "6"
        vaults = await handlers.get_vaults(self.ws, self.user)
        if vaults is None:
            vaults = []
        while key != "\n":
            pos = await self.navigate(
                key, self.window, y=6,
                length=len(vaults)
            )
            self.window.erase()
            self.window.box()
            self.window.addstr(0, 1, "Vaults")
            self.window.addstr(1, 1, "<Enter> select vault")
            self.window.addstr(2, 1, "<A> Add vault")
            self.window.addstr(3, 1, "<D> Delete vault")
            self.window.addstr(4, 1, "<R> Rename vault")
            self.window.addstr(5, 1, "<Esc> Main menu")
            for i, vault in enumerate(vaults):
                self.window.addstr(i + 6, 1, vault["name"])

            selected_string = self.window.instr(
                pos[0], 1, self.window.getmaxyx()[1] - 4
            ).decode("utf-8")
            self.window.addstr(pos[0], 1, " " + selected_string, self.hl_color)

            key = self.window.getkey()
            if key == "A":
                await self.vault_create()
            if key == "D":
                await self.vault_delete()
            if key == "R":
                await self.vault_rename()
            if ord(key) == 27:
                await self.main_menu()
                return

        self.vault = await handlers.get_vault(
            self.ws, self.user, vaults[pos[0] - 6]["name"], self.mkey
        )
        if self.vault is None:
            await self.message("Failed to select vault", self.error_color)
            await self.vaults_menu()
            return
        await self.message("Vault selected")
        await self.vaults_menu()

    async def account_logout(self):
        self.email = None
        self.mkey = None
        self.user = None
        self.vault = None
        await self.start_menu()

    async def vault_create(self):
        curses.echo()
        curses.curs_set(1)
        self.widget.erase()
        self.widget.box()
        self.widget.addstr(0, 1, "Create vault")
        name_field = "Vault name: "
        self.widget.addstr(1, 1, name_field)
        vault_name = self.widget.getstr(1, len(name_field) + 1).decode("utf-8")
        if not await handlers.create_vault(
            self.ws, self.user, vault_name, self.mkey
        ):
            await self.message("Failed to create vault", self.error_color)
            await self.vaults_menu()
            return
        await self.message("Vault created")
        await self.vaults_menu()

    # TODO: Convert these to use curses
    async def service_add(self, service):
        if self.user is None:
            print("You must be logged in to add a service")
            return
        if self.vault is None:
            print("No vault selected")
            return
        username = input("Enter the username: ")
        confirm_generate = input("Generate a password? (Y/n): ").lower()
        if confirm_generate == "n" or confirm_generate == "no":
            password = input("Enter the password: ")
        else:
            password = generate_password()
        notes = input("Enter any notes: ")
        self.vault.add(service, username, password, notes)
        self.vault.commit()
        await self.vault_save()
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

    async def service_delete(self, service_id):
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
        await self.vault_save()
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

    async def service_edit(self, service_id):
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
        confirm_generate = input("Generate a new password? (y/N): ").lower()
        if confirm_generate == "y" or confirm_generate == "yes":
            password = generate_password()
        else:
            password = input(f"Enter the new password ({entry['password']}): ")
            if password == "":
                password = entry["password"]
        notes = input(f"Enter the new notes ({entry['notes']}): ")
        if notes == "":
            notes = entry["notes"]
        self.vault.update(service_id, service, username, password, notes)
        self.vault.commit()
        await self.vault_save()
        print("Entry updated")

    # Vault commands
    async def vault_list(self):
        vaults = await handlers.get_vaults(self.ws, self.user)
        print("Vaults:")
        for vault in vaults:
            print(vault["name"])

    async def vault_select(self, vault_name):
        self.vault = await handlers.get_vault(
            self.ws, self.user, vault_name, self.mkey
        )
        if self.vault is None:
            print("Failed to select vault")
            return

    async def vault_rename(self):
        self.select_vault()
        new_name = input("Enter the new name for the vault: ")
        if new_name == "":
            print("No name entered")
            return
        self.vault.name = new_name
        if not await handlers.save_vault(self.ws, self.user, self.vault):
            print("Failed to rename vault")
            return
        print("Vault renamed")

    async def vault_delete(self):
        self.select_vault()
        confirmation = input(
            f"Are you sure you want to delete {self.vault.name}? (y/N): "
        ).lower()
        if confirmation != "y" or confirmation != "yes":
            print("Vault not deleted")
            return
        if not await handlers.delete_vault(
            self.ws, self.user, self.vault.name
        ):
            print("Failed to delete vault")
            return
        self.vault.rm()
        self.vault = None
        print("Vault deleted")

    async def vault_save(self):
        if self.vault is None:
            print("No vault selected")
            return
        if not await handlers.save_vault(self.ws, self.user, self.vault):
            print("Failed to save vault")
            return
        print("Vault saved")

    def vault_info(self):
        print(f"Vault: {self.vault.name}")

    # Account commands
    async def account_change_mkey(self):
        if self.user is None:
            print("You must be logged in to change your master password")
            return
        mkey = getpass.getpass("Enter your current master password: ")
        if mkey != self.mkey:
            print("Incorrect password - try again")
            await self.account_change_mkey()
            return
        new_mkey = getpass.getpass("Enter your new master password: ")
        confirm_mkey = getpass.getpass("Confirm your new master password: ")
        if new_mkey != confirm_mkey:
            print("Passwords do not match - try again")
            await self.account_change_mkey()
            return
        if await handlers.change_mkey(self.ws, self.user, mkey, new_mkey):
            self.mkey = new_mkey
            print("Master password changed")
        else:
            print("Failed to change master password")

    async def account_change_email(self):
        if self.user is None:
            print("You must be logged in to change your email")
            return
        new_email = input("Enter your new email: ")
        if await handlers.change_email(self.ws, self.user, new_email):
            self.email = new_email
            print("Email changed")
        else:
            print("Failed to change email")

    async def account_delete(self):
        if self.user is None:
            print("You must be logged in to delete your account")
            return
        confirmation = input(
            "Are you sure you want to delete your account? (y/N): "
        ).lower()
        if confirmation != "y" or confirmation != "yes":
            print("Account not deleted")
            return
        if await handlers.delete_account(self.ws, self.user):
            print("Account deleted")
        else:
            print("Failed to delete account")
