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
        self.searching = False

    async def run(self):
        try:
            self.redraw(self.menu)
            self.redraw(self.window)
            self.redraw(self.msgbox)
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
            self.message("INFO: Saving vault")
            self.vault.commit()
            await handlers.save_vault(self.ws, self.user, self.vault)
            self.vault.rm()
        self.message("INFO: Exiting")
        curses.echo()
        curses.curs_set(1)
        curses.endwin()
        if error is not None:
            print(error)
        sys.exit()

    def message(self, message, color=None):
        self.redraw(self.msgbox)
        if color is not None:
            self.msgbox.addstr(1, 1, message, color)
        else:
            self.msgbox.addstr(1, 1, message)
        self.msgbox.refresh()

    async def get_input(self, window, return_func, secret=False, init_str=""):
        curses.curs_set(1)
        key = window.getkey()
        string = init_str
        while self.escape(key) is False:
            if key == "KEY_BACKSPACE":
                if len(string) > 0:
                    string = string[:-1]
                    window.delch(window.getyx()[0], window.getyx()[1] - 1)
                    window.insch(" ")
                key = window.getkey()
                continue
            if key == "\n":
                curses.curs_set(0)
                return string
            string += key
            char = "*" if secret else key
            window.addch(char)
            key = window.getkey()
        self.redraw(window)
        curses.curs_set(0)
        return await return_func()

    async def navigate(self, key, window, y_offset, length):
        if length == 0:
            return (-1, -1)
        position = window.getyx()
        if key == "k" or key == "KEY_UP":
            position = (position[0] - 1, position[1])
        if key == "j" or key == "KEY_DOWN":
            position = (position[0] + 1, position[1])
        try:
            position = (y_offset + int(key) - 1, position[1])
        except ValueError:
            pass
        if position[0] < y_offset:
            position = (y_offset + length - 1, position[1])
        if position[0] > y_offset + length - 1:
            position = (y_offset, position[1])
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

    def select_string(self, window, y_offset, x_offset, length):
        if y_offset < 0:
            return
        selected_string = window.instr(
            y_offset, x_offset, length
        ).decode("utf-8")
        window.addstr(y_offset, x_offset, " " + selected_string, self.hl_color)

    # Menus
    async def start_menu(self):
        y_offset = 1
        key = f"{y_offset}"
        while self.escape(key) is False:
            pos = await self.navigate(key, self.menu, y_offset, 3)
            self.redraw(self.menu)
            self.menu.addstr(0, 1, "Menu")
            self.menu.addstr(y_offset, 1, "1. Login")
            self.menu.addstr(y_offset + 1, 1, "2. Register")
            self.menu.addstr(y_offset + 2, 1, "3. Exit")
            self.select_string(self.menu, pos[0], 1, self.menu_size[1] - 3)
            key = self.menu.getkey()

            if key == "\n":
                if pos[0] == y_offset:
                    await self.account_auth()
                elif pos[0] == y_offset + 1:
                    await self.account_register()
                elif pos[0] == y_offset + 2:
                    await self.exit()

    async def main_menu(self):
        y_offset = 1
        key = f"{y_offset}"
        while self.escape(key) is False:
            pos = await self.navigate(key, self.menu, y_offset, 5)
            self.redraw(self.menu)
            self.menu.addstr(0, 1, "Menu")
            self.menu.addstr(y_offset, 1, "1. Services")
            self.menu.addstr(y_offset + 1, 1, "2. Vault")
            self.menu.addstr(y_offset + 2, 1, "3. Settings")
            self.menu.addstr(y_offset + 3, 1, "4. Logout")
            self.menu.addstr(y_offset + 4, 1, "5. Exit")
            self.select_string(self.menu, pos[0], 1, self.menu_size[1] - 3)
            key = self.menu.getkey()

            if key == "\n":
                if pos[0] == y_offset:
                    await self.services_window()
                elif pos[0] == y_offset + 1:
                    await self.vault_window()
                elif pos[0] == y_offset + 2:
                    await self.settings_window()
                elif pos[0] == y_offset + 3:
                    await self.account_logout()
                elif pos[0] == y_offset + 4:
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
            return self.message(
                "ERROR: Failed to log in", self.error_color
            )
        self.redraw(self.window)
        self.message("INFO: Logged in")
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
            self.message(
                "ERROR: Passwords do not match", self.error_color
            )
            return await self.account_register()
        if not await handlers.register(self.ws, self.email, self.mkey):
            self.message(
                "ERROR: Failed to register", self.error_color
            )
            return await self.account_register()
        self.message("INFO: Registered")
        self.user = await handlers.auth(self.ws, self.email, self.mkey)
        if self.user is None:
            self.message("ERROR: Failed to log in", self.error_color)
            return await self.account_auth()
        self.message("INFO: Logged in")
        self.redraw(self.window)
        await self.main_menu()

    # Main menu windows
    async def services_window(self, search=None):
        y_offset = 7
        y_third = self.window_size[1] // 3
        hline = curses.ACS_HLINE
        vline = curses.ACS_VLINE
        if self.vault is None:
            self.message("ERROR: No vault selected", self.error_color)
            return await self.vault_window()
        key = f"{y_offset}"
        services = self.vault.services()
        if search is not None:
            query = re.compile(search, re.IGNORECASE)
            services = [
                service for service in services
                if query.search(service["service"])
            ]

        while self.escape(key) is False:
            if services is None:
                services = []
                self.message("ERROR: No services found", self.error_color)
            pos = await self.navigate(
                key, self.window, y_offset, len(services)
            )
            self.redraw(self.window)
            self.window.addstr(0, 1, "Services")
            self.window.hline(y_offset - 3, 1, hline, self.window_size[1] - 2)
            self.window.vline(1, y_third, vline, y_offset - 4)
            self.window.vline(1, y_third * 2, vline, y_offset - 4)
            self.window.addstr(1, 1, "<Y> Copy password")
            self.window.addstr(1, y_third + 1, "<Enter> Show service")
            self.window.addstr(1, y_third * 2 + 1, "<A> Add service")
            self.window.addstr(2, 1, "<D> Delete service")
            self.window.addstr(2, y_third + 1, "<E> Edit service")
            self.window.addstr(2, y_third * 2 + 1, "<ESC> Main menu")
            self.window.addstr(3, 1, "</> Search")

            self.window.hline(4, 1, hline, self.window_size[1] - 2)
            self.window.hline(6, 1, hline, self.window_size[1] - 2)
            self.window.hline(
                y_offset + len(services), 1, hline, self.window_size[1] - 2
            )
            self.window.vline(5, y_third, vline, 2 + len(services))
            self.window.vline(5, y_third * 2, vline, 2 + len(services))
            self.window.addstr(5, 1, "Service")
            self.window.addstr(5, y_third + 1, "Username")
            self.window.addstr(5, y_third * 2 + 1, "Notes")

            for i, service in enumerate(services):
                service_name = service["service"]
                user = service["user"]
                notes = service["notes"]
                if len(service_name) > y_third - 2:
                    service_name = service_name[:y_third - 5] + "..."
                if len(user) > y_third - 2:
                    user = user[:y_third - 5] + "..."
                if len(notes) > y_third - 2:
                    notes = notes[:y_third - 5] + "..."
                self.window.addstr(i + y_offset, 1, service_name)
                self.window.addstr(i + y_offset, y_third + 1, user)
                self.window.addstr(i + y_offset, y_third * 2 + 1, notes)

            self.select_string(self.window, pos[0], 1, y_third - 2)
            self.select_string(self.window, pos[0], y_third + 1, y_third - 2)
            self.select_string(
                self.window, pos[0], y_third * 2 + 1, y_third - 2
            )

            if self.searching:
                self.window.refresh()
                await self.search_services(search)
                return
            key = self.window.getkey()
            if services == []:
                service = None
            else:
                service = services[pos[0] - y_offset]
            match key:
                case "/":
                    if services != []:
                        await self.search_services()
                case "Y":
                    if service is not None:
                        await self.copy_password(service["id"])
                case "A":
                    await self.service_add()
                    services = self.vault.services()
                case "D":
                    if service is not None:
                        await self.service_delete(service["id"])
                        services = self.vault.services()
                case "E":
                    if service is not None:
                        await self.service_edit(service["id"])
                        services = self.vault.services()
                case "\n":
                    if service is not None:
                        await self.view_service(service)
        if search is not None:
            return await self.services_window()
        self.redraw(self.window)
        return await self.main_menu()

    async def vault_window(self):
        y_offset = 4
        y_third = self.window_size[1] // 3
        hline = curses.ACS_HLINE
        vline = curses.ACS_VLINE
        key = f"{y_offset}"
        vaults = await handlers.get_vaults(self.ws, self.user)
        while self.escape(key) is False:
            if vaults is None:
                vaults = []
                self.message("ERROR: No vaults found", self.error_color)
            pos = await self.navigate(key, self.window, y_offset, len(vaults))
            self.redraw(self.window)
            self.window.addstr(0, 1, "Vaults")
            self.window.hline(3, 1, hline, self.window_size[1] - 2)
            self.window.vline(1, y_third, vline, 2)
            self.window.vline(1, y_third * 2, vline, 2)
            self.window.addstr(1, 1, "<Enter> select vault")
            self.window.addstr(1, y_third + 1, "<A> Add vault")
            self.window.addstr(1, y_third * 2 + 1, "<D> Delete vault")
            self.window.addstr(2, 1, "<R> Rename vault")
            self.window.addstr(2, y_third + 1, "<ESC> Main menu")
            for i, vault in enumerate(vaults):
                self.window.addstr(i + y_offset, 1, vault["name"])
            self.select_string(self.window, pos[0], 1, self.window_size[1] - 3)

            vault = vaults[pos[0] - y_offset] if len(vaults) > 0 else None
            key = self.window.getkey()
            if key == "A":
                await self.vault_create()
                vaults = await handlers.get_vaults(self.ws, self.user)
            if key == "D":
                if vault is not None:
                    await self.vault_delete(vault["name"])
                    vaults = await handlers.get_vaults(self.ws, self.user)
            if key == "R":
                if vault is not None:
                    await self.vault_rename(vault)
                    vaults = await handlers.get_vaults(self.ws, self.user)
            if key == "\n":
                if vault is not None:
                    self.vault = await handlers.get_vault(
                        self.ws, self.user, vault["name"], self.mkey
                    )
                    if self.vault is None:
                        self.message(
                            "ERROR: Failed to select vault", self.error_color
                        )
                        return await self.vault_window()
                    self.message(f"INFO: Selected {self.vault.name}")
                    self.redraw(self.window)
                    return await self.services_window()
        self.redraw(self.window)
        return await self.main_menu()

    async def settings_window(self):
        y_offset = 1
        key = f"{y_offset}"
        while self.escape(key) is False:
            pos = await self.navigate(key, self.window, y_offset, 3)
            self.redraw(self.window)
            self.window.addstr(0, 1, "Settings")
            self.window.addstr(1, 1, "1. Change master password")
            self.window.addstr(2, 1, "2. Change email")
            self.window.addstr(3, 1, "3. Delete account")

            selected_string = self.window.instr(
                pos[0], 1, self.window_size[1] - 4
            ).decode("utf-8")
            self.window.addstr(pos[0], 1, " " + selected_string, self.hl_color)

            key = self.window.getkey()
            if key == "\n":
                if pos[0] == y_offset:
                    await self.account_change_mkey()
                elif pos[0] == y_offset + 1:
                    await self.account_change_email()
                elif pos[0] == y_offset + 2:
                    await self.account_delete()
        self.redraw(self.window)
        return await self.main_menu()

    async def account_logout(self):
        self.email = None
        self.mkey = None
        self.user = None
        self.vault = None
        self.screen.clear()
        self.message("INFO: Logged out")
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
            self.message(
                "ERROR: Failed to create vault", self.error_color
            )
            return await self.vault_window()
        self.message("INFO: Vault created")
        self.redraw(self.widget)

    async def vault_delete(self, vault_name):
        self.message(
            "CONFIRMATION: Are you sure you want to delete this vault? (y/N)"
        )
        confirmation = self.msgbox.getkey().lower()
        if confirmation != "y":
            return self.message(
                "ERROR: Vault not deleted", self.error_color
            )
        if not await handlers.delete_vault(self.ws, self.user, vault_name):
            return self.message(
                "ERROR: Failed to delete vault", self.error_color
            )
        if self.vault is not None and self.vault.name == vault_name:
            self.vault.rm()
            self.vault = None
        self.message(f"INFO: Delted vault {vault_name}")

    async def vault_rename(self, vault):
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Rename vault")
        name_field = "New vault name: " + vault["name"]
        self.widget.addstr(1, 1, name_field)
        self.widget.move(1, len(name_field) + 1)
        new_name = await self.get_input(
            self.widget, self.vault_window, init_str=vault["name"]
        )
        if new_name == "":
            self.message("ERROR: Invalid name", self.error_color)
            return self.redraw(self.widget, box=False)
        if not await handlers.update_vault_name(
            self.ws, self.user, vault["name"], new_name
        ):
            self.message(
                "ERROR: Failed to rename vault", self.error_color
            )
            return self.redraw(self.widget, box=False)
        self.message("INFO: Vault renamed")
        self.redraw(self.widget, box=False)

    # Service menu functions
    async def view_service(self, service):
        self.redraw(self.widget)
        self.widget.addstr(1, 1, f"Service: {service['service']}")
        self.widget.addstr(2, 1, f"Username: {service['user']}")
        self.widget.addstr(3, 1, f"Password: {service['password']}")
        self.widget.addstr(4, 1, f"Notes: {service['notes']}")
        self.widget.addstr(6, 1, "Press any key to continue")
        self.widget.refresh()
        self.widget.getkey()
        self.redraw(self.widget, box=False)

    async def copy_password(self, service_id):
        entry = self.vault.service(service_id)
        if entry is None:
            self.message("ERROR: Entry not found", self.error_color)
            return
        pyperclip.copy(entry["password"])
        self.message("INFO: Password copied to clipboard")

    async def service_add(self):
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Add service")
        password = generate_password()
        service_field = "Service name: "
        username_field = "Username: "
        notes_field = "Notes: "
        password_field = "Password: " + len(password) * "*"
        self.widget.addstr(1, 1, service_field)
        self.widget.addstr(2, 1, username_field)
        self.widget.addstr(3, 1, notes_field)
        self.widget.addstr(4, 1, password_field)
        self.widget.move(1, len(service_field) + 1)
        service = await self.get_input(self.widget, self.services_window)
        if service == "":
            self.message("ERROR: Invalid service name", self.error_color)
            return await self.service_add()
        self.widget.move(2, len(username_field) + 1)
        username = await self.get_input(self.widget, self.services_window)
        self.widget.move(3, len(notes_field) + 1)
        notes = await self.get_input(self.widget, self.services_window)
        self.widget.move(4, len(password_field) + 1)
        password = await self.get_input(
            self.widget, self.services_window,
            secret=True, init_str=password
        )
        self.vault.add(service, username, password, notes)
        self.vault.commit()
        await handlers.save_vault(self.ws, self.user, self.vault)
        self.message("INFO: Service added")

    async def service_delete(self, service_id):
        self.message(
            "CONFIRMATION: Are you sure you want to delete this entry? (y/N)"
        )
        confirmation = self.msgbox.getkey().lower()
        if confirmation != "y":
            return self.message(
                "ERROR: Entry not deleted", self.error_color
            )
        self.vault.delete(service_id)
        self.vault.commit()
        await handlers.save_vault(self.ws, self.user, self.vault)
        self.message("INFO: Entry deleted")

    async def service_edit(self, service_id):
        entry = self.vault.service(service_id)
        if entry is None:
            return self.message(
                "ERROR: Entry not found", self.error_color
            )
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Edit service")
        service_field = "Service name: " + entry["service"]
        username_field = "Username: " + entry["user"]
        notes_field = "Notes: " + entry["notes"]
        password_field = "Password: " + "*" * len(entry["password"])
        gen_pass_field = "Generate password (y/N): "
        self.widget.addstr(1, 1, service_field)
        self.widget.addstr(2, 1, username_field)
        self.widget.addstr(3, 1, notes_field)
        self.widget.addstr(4, 1, password_field)
        self.widget.addstr(5, 1, gen_pass_field)
        self.widget.move(1, len(service_field) + 1)
        service = await self.get_input(
            self.widget, self.services_window, init_str=entry["service"]
        )
        self.widget.move(2, len(username_field) + 1)
        username = await self.get_input(
            self.widget, self.services_window, init_str=entry["user"]
        )
        self.widget.move(3, len(notes_field) + 1)
        notes = await self.get_input(
            self.widget, self.services_window, init_str=entry["notes"]
        )
        self.widget.move(4, len(password_field) + 1)
        password = await self.get_input(
            self.widget, self.services_window,
            secret=True, init_str=entry["password"]
        )
        self.widget.move(5, len(gen_pass_field) + 1)
        gen_pass = self.widget.getkey().lower()
        if gen_pass == "y":
            password = generate_password()
            self.widget.addstr(4, 1, "Password: " + "*" * len(password))
            self.widget.refresh()
        self.msgbox.addstr(
            1, 1,
            "CONFIRMATION: Are you sure you want to update this entry? (y/N)"
        )
        confirmation = self.msgbox.getkey().lower()
        if confirmation != "y":
            return self.message(
                "ERROR: Entry not updated", self.error_color
            )
        self.vault.update(service_id, service, username, password, notes)
        self.vault.commit()
        await handlers.save_vault(self.ws, self.user, self.vault)
        self.message("INFO: Service updated")

    async def search_services(self, search=""):
        self.searching = True
        self.redraw(self.msgbox)
        search_prompt = "QUERY: " + search
        self.msgbox.addstr(1, 1, search_prompt)
        self.msgbox.move(1, len(search_prompt) + 1)
        key = self.msgbox.getkey()
        if self.escape(key):
            search = None
            self.searching = False
        elif key == "\n":
            self.searching = False
        elif key == "KEY_BACKSPACE":
            search = search[:-1]
        else:
            search += key
        return await self.services_window(search)

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
            self.widget, self.settings_window, secret=True
        )
        self.widget.move(2, len(new_field) + 1)
        new = await self.get_input(
            self.widget, self.settings_window, secret=True
        )
        self.widget.move(3, len(confirm_field) + 1)
        confirm = await self.get_input(
            self.widget, self.settings_window, secret=True
        )
        if new != confirm:
            self.message(
                "ERROR: Passwords do not match", self.error_color
            )
            return await self.account_change_mkey()
        if not await handlers.change_mkey(
            self.ws, self.user, current, new
        ):
            self.message(
                "ERROR: Failed to change password", self.error_color
            )
            return await self.account_change_mkey()
        self.mkey = new
        self.message("INFO: Password changed")

    async def account_change_email(self):
        self.redraw(self.widget)
        self.widget.addstr(0, 1, "Change email")
        email_field = "New email: "
        self.widget.addstr(1, 1, email_field)
        self.widget.move(1, len(email_field) + 1)
        new_email = await self.get_input(self.widget, self.settings_window)
        if not await handlers.change_email(self.ws, self.user, new_email):
            self.message(
                "ERROR: Failed to change email", self.error_color
            )
            return await self.account_change_email()
        self.email = new_email
        self.message("INFO: Email changed")

    async def account_delete(self):
        message = (
            "CONFIRMATION: Are you sure you want to delete your account? (y/N)"
        )
        self.msgbox.addstr(1, 1, message, self.hl_color)
        self.msgbox.move(1, len(message) + 1)
        self.msgbox.refresh()
        confirmation = self.msgbox.getkey().lower()
        if confirmation != "y":
            return self.message(
                "ERROR: Account not deleted", self.error_color
            )
        if not await handlers.delete_account(self.ws, self.user):
            return self.message(
                "ERROR: Failed to delete account", self.error_color
            )
        self.message("INFO: Account deleted")
        self.email = None
        self.mkey = None
        self.user = None
        self.vault = None
        self.redraw(self.window)
        await self.start_menu()
