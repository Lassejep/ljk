import pyperclip
import curses
import sys
import re
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
        self.menu.keypad(True)
        self.menu_size = self.menu.getmaxyx()
        self.menu_loc = self.menu.getbegyx()
        self.window = self.screen.subpad(
            self.screen_size[0] - 2, int(self.screen_size[1] * 0.8),
            0, int(self.screen_size[1] * 0.2)
        )
        self.window.keypad(True)
        self.window_size = self.window.getmaxyx()
        self.window_loc = self.window.getbegyx()
        self.widget = self.screen.subpad(
            int(self.window_size[0] * 0.6), int(self.window_size[1] * 0.6),
            self.window_loc[0] + int(self.window_size[0] * 0.2),
            self.window_loc[1] + int(self.window_size[1] * 0.2)
        )
        self.widget.keypad(True)
        self.widget_size = self.widget.getmaxyx()
        self.widget_loc = self.widget.getbegyx()
        self.msgbox = self.screen.subpad(
            3, self.window_size[1], self.window_size[0] - 1, self.window_loc[1]
        )
        self.msgbox.keypad(True)

        curses.noecho()
        curses.curs_set(0)
        curses.set_escdelay(10)
        curses.start_color()
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        self.text_color = curses.color_pair(0)
        self.hl_color = curses.color_pair(2)
        self.error_color = curses.color_pair(4)

    async def run(self):
        try:
            if self.user is not None:
                await self.main_menu()
            else:
                await self.start_menu()
        except Exception as e:
            await self.exit(e)
        except KeyboardInterrupt:
            await self.exit()

    async def exit(self, error=None):
        if self.vault is not None:
            await self.message("INFO: Saving vault")
            self.vault.commit()
            await handlers.save_vault(self.ws, self.user, self.vault)
            self.vault.rm()
        await self.message("INFO: Exiting")
        curses.echo()
        curses.curs_set(1)
        curses.endwin()
        if error is not None:
            print(error)
        sys.exit()

    async def message(self, message, color=None):
        self.redraw(self.msgbox)
        if color is not None:
            self.msgbox.addstr(1, 1, message, color)
        else:
            self.msgbox.addstr(1, 1, message)
        self.msgbox.noutrefresh()
        curses.doupdate()

    async def get_input(
            self, window, return_func, secret=False, initial_string=""
    ):
        curses.curs_set(1)
        key = window.getkey()
        string = initial_string
        while key != "\n":
            if key == "KEY_BACKSPACE":
                if len(string) > 0:
                    string = string[:-1]
                    window.delch(window.getyx()[0], window.getyx()[1] - 1)
                    window.insch(" ")
                key = window.getkey()
                continue
            if self.escape(key):
                self.redraw(window)
                curses.curs_set(0)
                return await return_func()
            string += key
            if secret:
                window.addch("*")
            else:
                window.addch(key)
            key = window.getkey()
        curses.curs_set(0)
        return string

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

    def escape(self, key):
        try:
            if ord(key) == 27:
                return True
        except TypeError:
            pass
        return False

    def redraw(self, window, box=True):
        window.erase()
        if box:
            window.box()
        window.refresh()

    # Menus
    async def start_menu(self):
        key = "1"
        while key != "\n":
            pos = await self.navigate(key, self.menu, y=1, length=3)
            self.redraw(self.menu)
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
        key = "1"
        while key != "\n":
            pos = await self.navigate(key, self.menu, y=1, length=5)
            self.redraw(self.menu)
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
            await self.services_window()
        elif pos[0] == 2:
            await self.vault_window()
        elif pos[0] == 3:
            await self.settings_menu()
        elif pos[0] == 4:
            await self.account_logout()
        elif pos[0] == 5:
            await self.exit()

    # Start menu windows
    async def account_auth(self):
        self.redraw(self.window)

        self.window.addstr(0, 1, "Login")
        email_field = "Enter your email: "
        password_field = "Enter your master password: "
        self.window.addstr(2, 1, email_field)
        self.window.addstr(3, 1, password_field)
        self.window.move(2, len(email_field) + 1)
        self.email = await self.get_input(self.window, self.start_menu)
        self.window.move(3, len(password_field) + 1)
        self.mkey = await self.get_input(
            self.window, self.start_menu, secret=True
        )
        self.user = await handlers.auth(self.ws, self.email, self.mkey)
        if self.user is None:
            return await self.message(
                "ERROR: Failed to log in", self.error_color
            )
        self.redraw(self.window)
        await self.message("INFO: Logged in")
        await self.main_menu()

    async def account_register(self):
        self.redraw(self.window)

        email_field = "Enter your email: "
        password_field = "Enter your master password: "
        confirm_field = "Repeat your master password: "
        self.window.addstr(0, 1, "Register")
        self.window.addstr(1, 1, email_field)
        self.window.addstr(2, 1, password_field)
        self.window.addstr(3, 1, confirm_field)
        self.window.move(1, len(email_field) + 1)
        self.email = await self.get_input(self.window, self.start_menu)
        self.window.move(2, len(password_field) + 1)
        self.mkey = await self.get_input(
            self.window, self.start_menu, secret=True
        )
        self.window.move(3, len(confirm_field) + 1)
        confirm_pass = await self.get_input(
            self.window, self.start_menu, secret=True
        )
        if self.mkey != confirm_pass:
            await self.message(
                "ERROR: Passwords do not match", self.error_color
            )
            return await self.account_register()
        if not await handlers.register(self.ws, self.email, self.mkey):
            await self.message(
                "ERROR: Failed to register", self.error_color
            )
            return await self.account_register()
        await self.message("INFO: Registered")
        self.user = await handlers.auth(self.ws, self.email, self.mkey)
        if self.user is None:
            await self.message("ERROR: Failed to log in", self.error_color)
            return await self.account_auth()
        await self.message("INFO: Logged in")
        self.redraw(self.window)
        await self.main_menu()

    # Main menu windows
    async def services_window(self):
        y_offset = 5
        if self.vault is None:
            await self.message("ERROR: No vault selected", self.error_color)
            return await self.main_menu()
        key = f"{y_offset}"
        services = self.vault.services()
        if services is None:
            services = []
        while key != "\n":
            pos = await self.navigate(
                key, self.window, y=y_offset,
                length=len(services)
            )
            self.redraw(self.window)
            self.window.addstr(0, 1, "Services")
            self.window.hline(
                y_offset - 1, 1, curses.ACS_HLINE, self.window_size[1] - 2
            )
            self.window.vline(
                1, self.window_size[1] // 3, curses.ACS_VLINE, y_offset - 2
            )
            self.window.vline(
                1, self.window_size[1] // 3 * 2, curses.ACS_VLINE, y_offset - 2
            )
            self.window.addstr(1, 1, "<Y> Copy password")
            self.window.addstr(
                1, self.window_size[1] // 3 + 1, "<Enter> Show service"
            )
            self.window.addstr(
                1, self.window_size[1] // 3 * 2 + 1, "<A> Add service"
            )
            self.window.addstr(2, 1, "<D> Delete service")
            self.window.addstr(
                2, self.window_size[1] // 3 + 1, "<E> Edit service"
            )
            self.window.addstr(
                2, self.window_size[1] // 3 * 2 + 1, "<ESC> Main menu"
            )
            self.window.addstr(3, 1, "</> Search")

            for i, service in enumerate(services):
                self.window.addstr(i + y_offset, 1, service["service"])
            selected_string = self.window.instr(
                pos[0], 1, self.window.getmaxyx()[1] - y_offset
            ).decode("utf-8")
            self.window.addstr(pos[0], 1, " " + selected_string, self.hl_color)

            if len(services) > 0:
                service = services[pos[0] - y_offset]
            else:
                service = None
            key = self.window.getkey()
            if key == "/":
                services = await self.search_services()
            if key == "Y":
                await self.copy_password(service["id"])
            if key == "A":
                await self.service_add()
                services = self.vault.services()
            if key == "D":
                await self.service_delete(service["id"])
                services = self.vault.services()
            if key == "E":
                await self.service_edit(service["id"])
                services = self.vault.services()
            if self.escape(key):
                self.redraw(self.window)
                return await self.main_menu()
        return await self.services_window()

    async def vault_window(self):
        key = "4"
        vaults = await handlers.get_vaults(self.ws, self.user)
        if vaults is None:
            vaults = []
        while key != "\n":
            pos = await self.navigate(
                key, self.window, y=4,
                length=len(vaults)
            )
            self.redraw(self.window)
            self.window.addstr(0, 1, "Vaults")
            self.window.hline(3, 1, curses.ACS_HLINE, self.window_size[1] - 2)
            self.window.vline(1, self.window_size[1] // 3, curses.ACS_VLINE, 2)
            self.window.vline(
                1, self.window_size[1] // 3 * 2, curses.ACS_VLINE, 2
            )
            self.window.addstr(1, 1, "<Enter> select vault")
            self.window.addstr(
                1, self.window_size[1] // 3 + 1, "<A> Add vault")
            self.window.addstr(
                1, self.window_size[1] // 3 * 2 + 1, "<D> Delete vault"
            )
            self.window.addstr(2, 1, "<R> Rename vault")
            self.window.addstr(
                2, self.window_size[1] // 3 + 1, "<ESC> Main menu"
            )
            for i, vault in enumerate(vaults):
                self.window.addstr(i + 4, 1, vault["name"])

            selected_string = self.window.instr(
                pos[0], 1, self.window.getmaxyx()[1] - 4
            ).decode("utf-8")
            self.window.addstr(pos[0], 1, " " + selected_string, self.hl_color)

            vault = vaults[pos[0] - 4] if len(vaults) > 0 else None
            key = self.window.getkey()
            if key == "A":
                await self.vault_create()
                vaults = await handlers.get_vaults(self.ws, self.user)
            if key == "D":
                await self.vault_delete(vault["name"])
                vaults = await handlers.get_vaults(self.ws, self.user)
            if key == "R":
                await self.vault_rename(vault)
                vaults = await handlers.get_vaults(self.ws, self.user)
            if self.escape(key):
                self.redraw(self.window)
                return await self.main_menu()

        self.vault = await handlers.get_vault(
            self.ws, self.user, vault["name"], self.mkey
        )
        if self.vault is None:
            await self.message(
                "ERROR: Failed to select vault", self.error_color
            )
            return await self.vault_window()
        await self.message(f"INFO: Selected {self.vault.name}")
        self.redraw(self.window)
        return await self.services_window()

    # TODO: Change the settings menu
    async def settings_menu(self):
        self.redraw(self.window)
        self.window.addstr(0, 1, "Settings")
        key = "4"
        while key != "\n":
            pos = await self.navigate(key, self.window, y=4, length=4)
            self.redraw(self.window)
            self.window.addstr(0, 1, "Settings")
            self.window.hline(3, 1, curses.ACS_HLINE, self.window_size[1] - 2)
            self.window.vline(1, self.window_size[1] // 3, curses.ACS_VLINE, 2)
            self.window.vline(
                1, self.window_size[1] // 3 * 2, curses.ACS_VLINE, 2
            )
            self.window.addstr(1, 1, "<C> Change master password")
            self.window.addstr(
                1, self.window_size[1] // 3 + 1, "<E> Change email")
            self.window.addstr(
                1, self.window_size[1] // 3 * 2 + 1, "<D> Delete account")
            self.window.addstr(2, 1, "<ESC> Main menu")

            selected_string = self.window.instr(
                pos[0], 1, self.window.getmaxyx()[1] - 4
            ).decode("utf-8")
            self.window.addstr(pos[0], 1, " " + selected_string, self.hl_color)

            key = self.window.getkey()
            if key == "C":
                await self.account_change_mkey()
            if key == "E":
                await self.account_change_email()
            if key == "D":
                await self.account_delete()
            if self.escape(key):
                self.redraw(self.window)
                return await self.main_menu()
        return await self.settings_menu()

    async def account_logout(self):
        self.email = None
        self.mkey = None
        self.user = None
        self.vault = None
        self.screen.clear()
        await self.message("INFO: Logged out")
        await self.start_menu()

    # Vault menu functions
    async def vault_create(self):
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Create vault")
        name_field = "Vault name: "
        self.widget.addstr(1, 1, name_field)
        self.widget.move(1, len(name_field) + 1)
        vault_name = await self.get_input(self.widget, self.vault_window)
        if not await handlers.create_vault(
            self.ws, self.user, vault_name, self.mkey
        ):
            await self.message("ERROR: Failed to create vault", self.error_color)
            return await self.vault_window()
        await self.message("INFO: Vault created")
        self.redraw(self.widget)

    async def vault_delete(self, vault_name):
        await self.message(
            "CONFIRMATION: Are you sure you want to delete this vault? (y/N)"
        )
        confirmation = self.msgbox.getkey().lower()
        if confirmation != "y":
            return await self.message(
                "ERROR: Vault not deleted", self.error_color
            )
        if not await handlers.delete_vault(self.ws, self.user, vault_name):
            return await self.message(
                "ERROR: Failed to delete vault", self.error_color
            )
        if self.vault is not None and self.vault.name == vault_name:
            self.vault.rm()
            self.vault = None
        await self.message(f"INFO: Delted vault {vault_name}")

    async def vault_rename(self, vault):
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Rename vault")
        name_field = "New vault name: " + vault["name"]
        self.widget.addstr(1, 1, name_field)
        self.widget.move(1, len(name_field) + 1)
        new_name = await self.get_input(
            self.widget, self.vault_window, initial_string=vault["name"]
        )
        if new_name == "":
            await self.message("ERROR: Invalid name", self.error_color)
            return self.redraw(self.widget, box=False)
        if not await handlers.update_vault_name(
            self.ws, self.user, vault["name"], new_name
        ):
            await self.message(
                "ERROR: Failed to rename vault", self.error_color
            )
            return self.redraw(self.widget, box=False)
        await self.message("INFO: Vault renamed")
        self.redraw(self.widget, box=False)

    # Service menu functions
    async def copy_password(self, service_id):
        entry = self.vault.service(service_id)
        if entry is None:
            await self.message("ERROR: Entry not found", self.error_color)
            return
        pyperclip.copy(entry["password"])
        await self.message("INFO: Password copied to clipboard")

    # TODO: Add a password generator
    async def service_add(self):
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Add service")
        service_field = "Service name: "
        username_field = "Username: "
        password_field = "Password: "
        notes_field = "Notes: "
        self.widget.addstr(1, 1, service_field)
        self.widget.addstr(2, 1, username_field)
        self.widget.addstr(3, 1, password_field)
        self.widget.addstr(4, 1, notes_field)
        self.widget.move(1, len(service_field) + 1)
        service = await self.get_input(self.widget, self.services_window)
        self.widget.move(2, len(username_field) + 1)
        username = await self.get_input(self.widget, self.services_window)
        self.widget.move(3, len(password_field) + 1)
        password = await self.get_input(
            self.widget, self.services_window, secret=True
        )
        self.widget.move(4, len(notes_field) + 1)
        notes = await self.get_input(self.widget, self.services_window)
        self.vault.add(service, username, password, notes)
        self.vault.commit()
        await handlers.save_vault(self.ws, self.user, self.vault)
        await self.message("INFO: Service added")

    async def service_delete(self, service_id):
        confirmation = await self.get_input(
            self.widget, self.services_window, secret=True
        )
        if confirmation != "y":
            return await self.message(
                "ERROR: Entry not deleted", self.error_color
            )
        self.vault.delete(service_id)
        self.vault.commit()
        await handlers.save_vault(self.ws, self.user, self.vault)
        await self.message("INFO: Entry deleted")

    # TODO: Add a password generator
    async def service_edit(self, service_id):
        entry = self.vault.service(service_id)
        if entry is None:
            return await self.message(
                "ERROR: Entry not found", self.error_color
            )
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Edit service")
        service_field = "Service name: " + entry["service"]
        username_field = "Username: " + entry["user"]
        password_field = "Password: " + "*" * len(entry["password"])
        notes_field = "Notes: " + entry["notes"]
        self.widget.addstr(1, 1, service_field)
        self.widget.addstr(2, 1, username_field)
        self.widget.addstr(3, 1, password_field)
        self.widget.addstr(4, 1, notes_field)
        self.widget.move(1, len(service_field) + 1)
        service = await self.get_input(
            self.widget, self.services_window, initial_string=entry["service"]
        )
        self.widget.move(2, len(username_field) + 1)
        username = await self.get_input(
            self.widget, self.services_window, initial_string=entry["user"]
        )
        self.widget.move(3, len(password_field) + 1)
        password = await self.get_input(
            self.widget, self.services_window,
            secret=True, initial_string=entry["password"]
        )
        self.widget.move(4, len(notes_field) + 1)
        notes = await self.get_input(self.widget, self.services_window)
        self.vault.update(service_id, service, username, password, notes)
        self.vault.commit()
        await handlers.save_vault(self.ws, self.user, self.vault)
        await self.message("INFO: Service updated")

    # TODO: Make the search function in real time
    async def search_services(self):
        self.redraw(self.msgbox)
        services = self.vault.services()
        search_prompt = "QUERY: "
        self.msgbox.addstr(1, 1, search_prompt)
        self.msgbox.move(1, len(search_prompt) + 1)
        search = await self.get_input(self.msgbox, self.services_window)
        if search == "":
            return services
        query = re.compile(search, re.IGNORECASE)
        return [
            service for service in services if query.search(service["service"])
        ]

    # Settings menu functions
    # TODO: Check the all the settings functions
    async def account_change_mkey(self):
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Change master password")
        current_field = "Current password: "
        new_field = "New password: "
        confirm_field = "Confirm new password: "
        self.widget.addstr(1, 1, current_field)
        self.widget.addstr(2, 1, new_field)
        self.widget.addstr(3, 1, confirm_field)
        self.widget.move(1, len(current_field) + 1)
        current = await self.get_input(
            self.widget, self.settings_menu, secret=True
        )
        self.widget.move(2, len(new_field) + 1)
        new = await self.get_input(
            self.widget, self.settings_menu, secret=True
        )
        self.widget.move(3, len(confirm_field) + 1)
        confirm = await self.get_input(
            self.widget, self.settings_menu, secret=True
        )
        if new != confirm:
            await self.message(
                "ERROR: Passwords do not match", self.error_color
            )
            return await self.account_change_mkey()
        if not await handlers.change_mkey(
            self.ws, self.user, current, new
        ):
            await self.message(
                "ERROR: Failed to change password", self.error_color
            )
            return await self.account_change_mkey()
        self.mkey = new
        await self.message("INFO: Password changed")

    async def account_change_email(self):
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Change email")
        email_field = "New email: "
        self.widget.addstr(1, 1, email_field)
        self.widget.move(1, len(email_field) + 1)
        new_email = await self.get_input(self.widget, self.settings_menu)
        if not await handlers.change_email(self.ws, self.user, new_email):
            await self.message(
                "ERROR: Failed to change email", self.error_color
            )
            return await self.account_change_email()
        self.email = new_email
        await self.message("INFO: Email changed")

    async def account_delete(self):
        confirmation = await self.get_input(
            self.widget, self.settings_menu, secret=True
        )
        if confirmation != "y":
            return await self.message(
                "ERROR: Account not deleted", self.error_color
            )
        if not await handlers.delete_account(self.ws, self.user):
            return await self.message(
                "ERROR: Failed to delete account", self.error_color
            )
        await self.message("INFO: Account deleted")
        self.email = None
        self.mkey = None
        self.user = None
        self.vault = None
        await self.start_menu()
