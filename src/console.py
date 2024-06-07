import curses
from curses import textpad
import pyperclip
import re
from . import client
from .encryption import generate_password


# TODO: Add password length option
class Console:
    def __init__(self, ws, screen):
        self.ws = ws
        self.screen = screen
        self.screen_size = screen.getmaxyx()
        self.running = False
        curses.set_escdelay(10)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        self.text_color = curses.color_pair(0)
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_WHITE)
        self.background_color = curses.color_pair(1)
        self.hl_color = curses.color_pair(2)
        self.error_color = curses.color_pair(4)

        self.user = None
        self.vault = None

        self.msgbox = MessageBox(self)
        self.start_menu = StartMenu(self)
        self.login = LoginWidget(self)
        self.register = RegisterWidget(self)
        self.main_menu = MainMenu(self)
        self.settings_window = SettingsWindow(self)
        self.change_mpass = ChangeMpassWidget(self)
        self.change_email = ChangeEmailWidget(self)
        self.delete_account = DeleteAccountWidget(self)
        self.vault_window = VaultWindow(self)
        self.add_vault = AddVaultWidget(self)
        self.rename_vault = RenameVaultWidget(self)
        self.services_window = ServiceWindow(self)
        self.show_service = ShowServiceWidget(self)
        self.add_service = AddServiceWidget(self)
        self.edit_service = EditServiceWidget(self)

    async def run(self):
        self.running = True
        while self.running:
            if self.user is None:
                self.main_menu.menu.erase()
                await self.start_menu.run()
            else:
                self.start_menu.menu.erase()
                await self.main_menu.run()
        if self.vault is not None:
            await client.save_vault(self.ws, self.user, self.vault)

    def escape(self, key):
        try:
            if ord(key) == 27:
                return True
        except TypeError:
            pass
        return False

    def center(self, size, text):
        return (size[1] - len(text)) // 2

    async def start_select(self):
        if self.start_menu.pos[0] == 0:
            self.user = await self.login.run()
        if self.start_menu.pos[0] == 1:
            await self.register.run()
        if self.start_menu.pos[0] == 2:
            self.running = False

    async def main_select(self):
        if self.main_menu.pos[0] == 0:
            await self.services_window.run()
        if self.main_menu.pos[0] == 1:
            await self.vault_window.run()
        if self.main_menu.pos[0] == 2:
            await self.settings_window.run()
        if self.main_menu.pos[0] == 3:
            self.user = None
            self.vault = None
            self.main_menu.pos = (0, 0)
            self.main_menu.running = False
            self.msgbox.info("Logged out")
        if self.main_menu.pos[0] == 4:
            self.running = False


class MessageBox:
    def __init__(self, console):
        self.console = console
        self.size = (3, self.console.screen_size[1] * 4 // 5)
        self.box = self.console.screen.subpad(
            self.size[0], self.size[1],
            self.console.screen_size[0] - self.size[0],
            self.console.screen_size[1] - self.size[1]
        )
        self.loc = self.box.getbegyx()
        self.msgbox = self.box.subpad(
            self.size[0] - 2, self.size[1] - 2,
            self.loc[0] + 1, self.loc[1] + 1
        )
        self.size = self.msgbox.getmaxyx()
        self.loc = self.msgbox.getbegyx()
        self.msgbox.keypad(True)
        self.title = "Messages"
        self.error_color = self.console.error_color
        self.search_prompt = "Search: "
        self.search_field = self.msgbox.subpad(
            0, self.size[1] - len(self.search_prompt),
            self.loc[0], self.loc[1] + len(self.search_prompt)
        )
        self.search_field.keypad(True)
        self.search_box = textpad.Textbox(self.search_field, insert_mode=True)
        self.query = None

    def draw_box(self):
        self.box.erase()
        self.box.box()
        self.box.addstr(0, 1, self.title)
        self.box.refresh()

    def info(self, message):
        self.msgbox.erase()
        self.draw_box()
        self.msgbox.addstr(0, 0, f"INFO: {message}")
        self.msgbox.refresh()

    def error(self, message):
        self.msgbox.erase()
        self.draw_box()
        self.msgbox.addstr(0, 0, f"ERROR: {message}", self.error_color)
        self.msgbox.refresh()

    def confirm(self, message):
        self.msgbox.erase()
        self.draw_box()
        self.msgbox.addstr(0, 0, f"CONFIRM: {message} [y/N]")
        self.msgbox.refresh()
        if self.msgbox.getkey().lower() == "y":
            return True
        return False

    def clear(self):
        self.box.erase()
        self.box.refresh()
        self.msgbox.erase()
        self.msgbox.refresh()

    def search_validate(self, key):
        if key == 27:
            self.query = None
            self.console.services_window.update_service_list()
            return 7
        if key > 32 or key < 126:
            self.query = self.search_box.gather().strip() + chr(key)
            self.console.services_window.update_service_list()
        if key == 8:
            self.query = self.search_box.gather().strip()[:-2]
            self.console.services_window.update_service_list()
        if key == 10:
            return 7
        return key

    def search(self):
        self.msgbox.erase()
        self.draw_box()
        self.msgbox.addstr(0, 0, self.search_prompt)
        self.msgbox.refresh()
        if self.query is not None:
            self.search_field.addstr(0, 0, self.query)
        self.search_field.refresh()
        curses.curs_set(1)
        self.query = self.search_box.edit(self.search_validate).strip()
        curses.curs_set(0)
        self.console.services_window.update_service_list()
        if self.query is None:
            self.msgbox.erase()
        self.msgbox.refresh()


class Menu:
    def __init__(self, console, title):
        self.console = console
        self.title = title
        self.box_size = (
            self.console.screen_size[0], self.console.screen_size[1] // 5
        )
        self.box = self.console.screen.subpad(
            self.box_size[0], self.box_size[1], 0, 0
        )
        self.loc = self.box.getbegyx()
        self.menu = self.box.subpad(
            self.box_size[0] - 2, self.box_size[1] - 2,
            self.loc[0] + 1, self.loc[1] + 1
        )
        self.size = self.menu.getmaxyx()
        self.loc = self.menu.getbegyx()
        self.menu.keypad(True)
        self.pos = (0, 0)

    def draw(self):
        self.menu.erase()
        self.draw_box()
        self.draw_options()
        self.menu.refresh()

    def draw_box(self):
        self.box.box()
        self.box.addstr(0, 1, self.title)
        self.box.refresh()

    def draw_options(self):
        if self.options is None:
            return
        for i, option in enumerate(self.options):
            if i == self.pos[0]:
                self.menu.addstr(
                    i, 1, option, self.console.hl_color
                )
            else:
                self.menu.addstr(i, 0, option)

    async def navigate(self):
        key = self.menu.getkey()
        if key == "k" or key == "KEY_UP":
            self.pos = ((self.pos[0] - 1) % len(self.options), self.pos[1])
        if key == "j" or key == "KEY_DOWN":
            self.pos = ((self.pos[0] + 1) % len(self.options), self.pos[1])
        if key == "\n":
            await self.select()
        if self.console.escape(key):
            self.running = False
        self.draw()


class StartMenu(Menu):
    def __init__(self, console):
        super().__init__(console, "Start Menu")
        self.options = ["1. Login", "2. Register", "3. Exit"]

    async def run(self):
        self.running = True
        self.menu.erase()
        while self.running:
            self.draw()
            await self.navigate()
            self.menu.erase()

    async def select(self):
        self.running = False
        if self.pos[0] == 0:
            await self.console.login.run()
        if self.pos[0] == 1:
            await self.console.register.run()
        if self.pos[0] == 2:
            self.console.running = False


class MainMenu(Menu):
    def __init__(self, console):
        super().__init__(console, title="Main Menu")
        self.options = [
            "1. Services", "2. Vaults", "3. Settings", "4. Logout", "5. Exit"
        ]

    async def run(self):
        self.running = True
        self.menu.erase()
        curses.curs_set(0)
        while self.running:
            self.draw()
            await self.navigate()
            self.menu.erase()

    async def select(self):
        self.running = False
        if self.pos[0] == 0:
            if self.console.vault is None:
                self.console.msgbox.error("No vault selected")
                self.pos = (1, 0)
                self.draw()
                await self.console.vault_window.run()
            else:
                await self.console.services_window.run()
        if self.pos[0] == 1:
            await self.console.vault_window.run()
        if self.pos[0] == 2:
            await self.console.settings_window.run()
        if self.pos[0] == 3:
            if self.console.vault is not None:
                await client.save_vault(
                    self.console.ws, self.console.user, self.console.vault
                )
            self.console.user = None
            self.console.vault = None
            self.pos = (0, 0)
            self.running = False
            self.console.msgbox.info("Logged out")
        if self.pos[0] == 4:
            self.console.running = False


class Window:
    def __init__(self, console, title):
        self.console = console
        self.title = title
        self.box_size = (
            self.console.screen_size[0] - 3,
            self.console.screen_size[1] * 4 // 5
        )
        self.box = self.console.screen.subpad(
            self.box_size[0], self.box_size[1],
            0, self.console.screen_size[1] - self.box_size[1]
        )
        self.loc = self.box.getbegyx()
        self.window = self.box.subpad(
            self.box_size[0] - 2, self.box_size[1] - 2,
            self.loc[0] + 1, self.loc[1] + 1
        )
        self.size = self.window.getmaxyx()
        self.loc = self.window.getbegyx()
        self.window.keypad(True)
        self.keybinds = None
        self.options = None
        self.y_offset = 0
        self.pos = (0, 0)

    def draw(self):
        self.draw_box()
        self.draw_keybinds()
        self.draw_options()
        self.window.refresh()

    def draw_box(self):
        self.box.erase()
        self.box.box()
        self.box.addstr(0, 1, self.title)
        self.box.refresh()

    def draw_keybinds(self):
        if self.keybinds is None:
            return
        linelist, remainders = self.calculate_keybinds_height()
        padding = self.get_keybind_padding(linelist, remainders)
        self.y_offset = len(linelist) + 1
        for i, line in enumerate(linelist):
            x_offset = 0
            for j, keybind in enumerate(line):
                keybind = padding[i] + keybind + padding[i] + "|"
                self.window.addstr(
                    i, x_offset, keybind
                )
                x_offset += len(keybind)
        self.window.hline(i + 1, 0, curses.ACS_HLINE, self.size[1])

    def draw_options(self):
        if self.options is None:
            return
        for i, option in enumerate(self.options):
            if type(option) is str:
                if i == self.pos[0]:
                    self.window.addstr(
                        i + self.y_offset, 1, option, self.console.hl_color
                    )
                else:
                    self.window.addstr(i + self.y_offset, 0, option)
            elif type(option) is tuple:
                self.draw_cols(
                    self.window, i + self.y_offset, 0,
                    option, self.pos[0] == i
                )

    def draw_cols(self, window, y_offset, x_offset, option, selected):
        length = self.size[1] // len(option)
        for i, col in enumerate(option):
            if selected:
                window.addstr(
                    y_offset, x_offset + 1, col, self.console.hl_color
                )
                window.vline(
                    y_offset, x_offset + length - 1, curses.ACS_VLINE, 1
                )
            else:
                window.addstr(y_offset, x_offset, col)
                window.vline(
                    y_offset, x_offset + length - 1, curses.ACS_VLINE, 1
                )
            x_offset += length

    async def navigate(self):
        key = self.window.getkey()
        if key == "k" or key == "KEY_UP":
            self.pos = ((self.pos[0] - 1) % len(self.options), self.pos[1])
        if key == "j" or key == "KEY_DOWN":
            self.pos = ((self.pos[0] + 1) % len(self.options), self.pos[1])
        if key == "\n":
            await self.select()
        if self.console.escape(key):
            self.running = False
        self.draw()

    def calculate_keybinds_height(self):
        linelist = [[]]
        y_offset = 0
        x_offset = 0
        remainders = []
        for i, keybind in enumerate(self.keybinds):
            if x_offset + len(keybind) + 3 > self.size[1]:
                remainders.append((self.size[1]) - x_offset)
                y_offset += 1
                x_offset = 0
                linelist.append([])
            linelist[y_offset].append(keybind)
            x_offset += len(keybind) + 3
        remainders.append((self.size[1]) - x_offset)
        assert len(linelist) == len(remainders)
        return linelist, remainders

    def get_keybind_padding(self, linelist, remainders):
        padding = []
        for i, line in enumerate(linelist):
            pad = (remainders[i] // len(line)) // 2
            pad = pad if pad > 0 else 1
            padding.append(" " * pad)
        return padding


# TODO: Add search functionality
class ServiceWindow(Window):
    def __init__(self, console):
        super().__init__(console, "Services")
        self.keybinds = [
            "<Y> Copy password", "<Enter> Show service",
            "<A> Add service", "<D> Delete service",
            "<E> Edit service", "</> Search", "<ESC> Main menu"
        ]
        self.service_list = None

    async def run(self):
        self.running = True
        self.window.erase()
        self.update_service_list()
        while self.running:
            self.draw()
            await self.navigate()
            self.window.erase()
        self.window.refresh()

    async def navigate(self):
        key = self.window.getkey()
        if self.console.escape(key):
            if self.console.msgbox.query is not None:
                self.console.msgbox.query = None
                self.console.msgbox.msgbox.erase()
                self.console.msgbox.msgbox.refresh()
                self.update_service_list()
            else:
                self.running = False
        if key.lower() == "a":
            self.console.add_service.run()
            self.update_service_list()
            await client.save_vault(
                self.console.ws, self.console.user, self.console.vault
            )
        if key == "/":
            self.console.msgbox.search()
        if self.options is not None:
            if key == "k" or key == "KEY_UP":
                self.pos = ((self.pos[0] - 1) % len(self.options), self.pos[1])
            if key == "j" or key == "KEY_DOWN":
                self.pos = ((self.pos[0] + 1) % len(self.options), self.pos[1])
            if key == "\n":
                self.console.show_service.run(self.service_list[self.pos[0]])
            if key.lower() == "d":
                self.delete_service()
                self.update_service_list()
                await client.save_vault(
                    self.console.ws, self.console.user, self.console.vault
                )
            if key.lower() == "e":
                self.console.edit_service.run(self.service_list[self.pos[0]])
                self.update_service_list()
                await client.save_vault(
                    self.console.ws, self.console.user, self.console.vault
                )
            if key.lower() == "y":
                self.copy_password()
        self.draw()

    def update_service_list(self):
        if self.console.vault is None:
            self.options = None
            return
        self.service_list = self.console.vault.services()
        if self.console.msgbox.query is not None:
            self.service_list = [
                service for service in self.service_list
                if re.search(
                    self.console.msgbox.query, service["service"],
                    re.IGNORECASE
                ) is not None
            ]
            if self.service_list == 0:
                self.options = None
                return
        if self.service_list is None:
            self.options = None
            return
        else:
            self.options = [
                (service["service"], service["user"], service["notes"])
                for service in self.service_list
            ]
        self.draw()

    def delete_service(self):
        if not self.console.msgbox.confirm(
            "Are you sure you want to delete this service?"
        ):
            self.console.msgbox.info("Service not deleted")
            return
        service = self.service_list[self.pos[0]]
        self.console.vault.delete(service["id"])
        self.pos = (0, 0)
        self.console.msgbox.info("Service deleted")

    def copy_password(self):
        service = self.service_list[self.pos[0]]
        pyperclip.copy(service["password"])
        self.console.msgbox.info("Password copied")


class VaultWindow(Window):
    def __init__(self, console):
        super().__init__(console, "Vaults")
        self.keybinds = [
            "<Enter> Select vault", "<A> Add vault",
            "<D> Delete vault", "<R> Rename vault", "<ESC> Main menu"
        ]
        self.options = None
        self.vault_list = None

    async def run(self):
        self.running = True
        self.window.erase()
        await self.update_vault_list()
        while self.running:
            self.draw()
            await self.navigate()
            self.window.erase()
        self.window.refresh()

    async def navigate(self):
        key = self.window.getkey()
        if self.console.escape(key):
            self.running = False
        if key.lower() == "a":
            await self.console.add_vault.run()
            await self.update_vault_list()
        if self.options is not None:
            if key == "k" or key == "KEY_UP":
                self.pos = ((self.pos[0] - 1) % len(self.options), self.pos[1])
            if key == "j" or key == "KEY_DOWN":
                self.pos = ((self.pos[0] + 1) % len(self.options), self.pos[1])
            if key == "\n":
                await self.select()
            if key.lower() == "d":
                await self.delete_vault()
            if key.lower() == "r":
                await self.console.rename_vault.run(self.options[self.pos[0]])
                await self.update_vault_list()
        self.draw()

    async def update_vault_list(self):
        self.vault_list = await client.get_vaults(
            self.console.ws, self.console.user
        )
        if self.vault_list is None:
            self.options = None
        else:
            self.options = [vault["name"] for vault in self.vault_list]
        self.draw()

    async def select(self):
        if self.options is None:
            return
        vault = self.vault_list[self.pos[0]]
        self.console.vault = await client.get_vault(
            self.console.ws, self.console.user, vault["name"]
        )
        self.console.msgbox.info(
            f"Selected vault: {self.console.vault.name}"
        )
        self.running = False
        self.console.main_menu.pos = (0, 0)
        self.console.main_menu.draw()
        await self.console.main_menu.select()

    async def delete_vault(self):
        if not self.console.msgbox.confirm(
            "Are you sure you want to delete this vault?"
        ):
            self.console.msgbox.info("Vault not deleted")
            return
        vault_name = self.options[self.pos[0]]
        if not await client.delete_vault(
            self.console.ws, self.console.user, vault_name
        ):
            self.console.msgbox.error("Failed to delete vault")
        await self.update_vault_list()
        self.pos = (0, 0)
        self.console.msgbox.info("Vault deleted")


class SettingsWindow(Window):
    def __init__(self, console):
        super().__init__(console, "Settings")
        self.options = [
            "1. Change master password", "2. Change email",
            "3. Delete account"
        ]

    async def run(self):
        self.running = True
        self.window.erase()
        while self.running:
            self.draw()
            await self.navigate()
            self.window.erase()
        self.window.refresh()

    async def select(self):
        self.running = False
        if self.pos[0] == 0:
            await self.console.change_mpass.run()
        if self.pos[0] == 1:
            await self.console.change_email.run()
        if self.pos[0] == 2:
            await self.console.delete_account.run()


class InputForm:
    def __init__(
        self, widget, prompt, pos, init_str="", secret=False, height=1
    ):
        self.widget = widget
        self.widget_window = widget.widget
        self.widget_size = self.widget_window.getmaxyx()
        self.prompt = prompt
        self.init_str = init_str
        self.height = height
        self.secret = secret
        self.pos = pos
        loc = self.widget_window.getbegyx()
        self.input_field = self.widget_window.subpad(
            self.height, self.widget_size[1] - len(self.prompt),
            loc[0] + self.pos[0], loc[1] + self.pos[1] + len(self.prompt)
        )
        self.textbox = textpad.Textbox(self.input_field, insert_mode=True)
        self.background_color = curses.color_pair(1)

    def draw(self):
        self.widget_window.addstr(self.pos[0], self.pos[1], self.prompt)
        if self.secret:
            self.input_field.attron(self.background_color)
        self.input_field.addstr(0, 0, self.init_str)
        self.input_field.refresh()

    def validate(self, key):
        if key == 27:
            self.running = False
            self.widget.running = False
            self.widget.clear()
            return 7
        if key == 10:
            return 7
        return key

    def get_input(self):
        if len(self.init_str) > 0:
            self.input_field.move(0, len(self.init_str))
        else:
            self.input_field.move(0, 0)
        curses.curs_set(1)
        out = self.textbox.edit(self.validate)
        curses.curs_set(0)
        if not self.widget.running:
            return None
        return out.strip()


class Widget:
    def __init__(self, console, title):
        self.console = console
        self.title = title
        self.box_size = (
            self.console.screen_size[0] // 2, self.console.screen_size[1] // 2
        )
        self.box = self.console.screen.subpad(
            self.box_size[0], self.box_size[1],
            self.console.screen_size[0] // 4, self.console.screen_size[1] // 4
        )
        loc = self.box.getbegyx()
        self.widget = self.box.subpad(
            self.box_size[0] - 2, self.box_size[1] - 2,
            loc[0] + 1, loc[1] + 1
        )
        self.size = self.widget.getmaxyx()
        self.loc = self.widget.getbegyx()
        self.widget.keypad(True)
        self.text_fields = None

    def draw(self):
        self.draw_box()
        if self.text_fields is not None:
            for text_field in self.text_fields:
                text_field.draw()
        self.widget.refresh()

    def draw_box(self):
        self.box.box()
        self.box.addstr(0, 1, self.title)
        self.box.refresh()

    def clear(self):
        self.box.erase()
        self.box.refresh()
        if self.text_fields is not None:
            for text_field in self.text_fields:
                text_field.input_field.erase()
                text_field.input_field.refresh()
        self.widget.erase()
        self.widget.refresh()


class LoginWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Login")
        self.console = console
        self.email_form = InputForm(self, "Email: ", (0, 0))
        self.mpass_form = InputForm(
            self, "Master password: ", (1, 0), secret=True
        )
        self.text_fields = [self.email_form, self.mpass_form]

    async def run(self):
        self.running = True
        self.draw()
        email = self.email_form.get_input()
        if email is None:
            self.clear()
            return None
        if len(email) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return None
        mpass = self.mpass_form.get_input()
        if mpass is None:
            self.clear()
            return None
        if len(mpass) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return None
        user = await client.auth(self.console.ws, email, mpass)
        if user is None:
            self.console.msgbox.error("Failed to login")
            self.clear()
            return None
        self.console.msgbox.info("Logged in")
        self.clear()
        self.console.user = user


class RegisterWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Register")
        self.email_form = InputForm(self, "Email: ", (0, 0))
        self.mpass_form = InputForm(
            self, "Master password: ", (1, 0), secret=True
        )
        self.repeat_mpass_form = InputForm(
            self, "Repeat master password: ", (2, 0), secret=True
        )
        self.text_fields = [
            self.email_form, self.mpass_form, self.repeat_mpass_form
        ]

    async def run(self):
        self.running = True
        self.draw()
        email = self.email_form.get_input()
        if email is None:
            self.clear()
            return
        if len(email) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return
        mpass = self.mpass_form.get_input()
        if mpass is None:
            self.clear()
            return
        if len(mpass) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return
        repeat_mpass = self.repeat_mpass_form.get_input()
        if repeat_mpass is None:
            self.clear()
            return
        if mpass != repeat_mpass:
            self.console.msgbox.error("Passwords do not match")
            self.clear()
            return
        if not await client.register(self.console.ws, email, mpass):
            self.console.msgbox.error("Failed to register")
            self.clear()
            return
        self.console.msgbox.info("Registered")
        self.clear()


class DeleteAccountWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Delete account")
        self.mpass_form = InputForm(
            self, "Master password: ", (0, 0), secret=True
        )
        self.text_fields = [self.mpass_form]

    async def run(self):
        self.running = True
        self.draw()
        mpass = self.mpass_form.get_input()
        if mpass is None:
            self.clear()
            return
        if len(mpass) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return
        if not self.console.msgbox.confirm(
            "Are you sure you want to delete your account?"
        ):
            self.console.msgbox.info("Account not deleted")
            self.clear()
            return
        if not await client.delete_account(
            self.console.ws, self.console.user, mpass
        ):
            self.console.msgbox.error("Failed to delete account")
            self.clear()
            return
        self.console.msgbox.info("Account deleted")
        self.clear()
        self.console.vault = None
        self.console.user = None


class ChangeEmailWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Change email")
        self.email_form = InputForm(self, "New Email: ", (0, 0))
        self.mpass_form = InputForm(
            self, "Master password: ", (1, 0), secret=True
        )
        self.text_fields = [self.email_form, self.mpass_form]

    async def run(self):
        self.running = True
        self.draw()
        new_email = self.email_form.get_input()
        if new_email is None:
            self.clear()
            return
        if len(new_email) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return
        mpass = self.mpass_form.get_input()
        if mpass is None:
            self.clear()
            return
        if len(mpass) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return
        if not await client.change_email(
            self.console.ws, self.console.user, new_email, mpass
        ):
            self.console.msgbox.error("Failed to change email")
            self.clear()
            return
        self.console.user = await client.auth(
            self.console.ws, new_email, mpass
        )
        self.console.msgbox.info("Email changed")
        self.clear()


class ChangeMpassWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Change master password")
        self.old_mpass_form = InputForm(
            self, "Old master password: ", (0, 0), secret=True
        )
        self.new_mpass_form = InputForm(
            self, "New master password: ", (1, 0), secret=True
        )
        self.repeat_new_mpass_form = InputForm(
            self, "Repeat new master password:",
            (2, 0), secret=True
        )
        self.text_fields = [
            self.old_mpass_form, self.new_mpass_form,
            self.repeat_new_mpass_form
        ]

    async def run(self):
        self.running = True
        self.draw()
        old_mpass = self.old_mpass_form.get_input()
        if old_mpass is None:
            self.clear()
            return
        if len(old_mpass) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return
        new_mpass = self.new_mpass_form.get_input()
        if new_mpass is None:
            self.clear()
            return
        if len(new_mpass) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return
        repeat_new_mpass = self.repeat_new_mpass_form.get_input()
        if repeat_new_mpass is None:
            self.clear()
            return
        if new_mpass != repeat_new_mpass:
            self.console.msgbox.error("Passwords do not match")
            self.clear()
            return
        if not await client.change_mkey(
            self.console.ws, self.console.user, old_mpass, new_mpass
        ):
            self.console.msgbox.error("Failed to change master password")
            self.clear()
            return
        self.console.user = await client.auth(
            self.console.ws, self.console.user["email"], new_mpass
        )
        self.console.msgbox.info("Master password changed")
        self.clear()


class AddVaultWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Add vault")
        self.vault_name_form = InputForm(self, "Vault name: ", (0, 0))
        self.text_fields = [self.vault_name_form]

    async def run(self):
        self.running = True
        self.draw()
        vault_name = self.vault_name_form.get_input()
        if vault_name is None:
            self.clear()
            return
        if vault_name == "":
            self.clear()
            return
        if not await client.create_vault(
            self.console.ws, self.console.user, vault_name
        ):
            self.console.msgbox.error("Failed to create vault")
            self.clear()
            return
        self.console.msgbox.info("Vault created")
        self.clear()


class RenameVaultWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Rename vault")
        self.vault_name_form = InputForm(
            self, "New vault name: ", (0, 0))
        self.text_fields = [self.vault_name_form]

    async def run(self, vault_name):
        self.running = True
        self.draw()
        new_vault_name = self.vault_name_form.get_input()
        if new_vault_name is None:
            self.clear()
            return
        if new_vault_name == "":
            self.clear()
            return
        if not await client.update_vault_name(
            self.console.ws, self.console.user, vault_name, new_vault_name
        ):
            self.console.msgbox.error("Failed to rename vault")
            self.clear()
            return
        self.console.msgbox.info("Vault renamed")
        self.clear()


class AddServiceWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Add service")
        self.service_form = InputForm(self, "Service: ", (0, 0))
        self.username_form = InputForm(self, "Username: ", (1, 0))
        self.password_form = InputForm(self, "Password: ", (2, 0))
        self.notes_form = InputForm(self, "Notes: ", (3, 0))
        self.text_fields = [
            self.service_form, self.username_form,
            self.password_form, self.notes_form
        ]

    def run(self):
        self.running = True
        self.password_form.init_str = generate_password()
        self.draw()
        service_name = self.service_form.get_input()
        if service_name is None:
            self.clear()
            return
        if service_name == "":
            self.console.msgbox.error("Service name cannot be empty")
            self.clear()
            return
        username = self.username_form.get_input()
        if username is None:
            self.clear()
            return
        password = self.password_form.get_input()
        if password is None:
            self.clear()
            return
        notes = self.notes_form.get_input()
        if notes is None:
            self.clear()
            return
        self.console.vault.add(
            service=service_name, user=username, password=password, notes=notes
        )
        self.console.msgbox.info("Service created")
        self.clear()


class EditServiceWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Edit service")

    def run(self, service):
        self.service_form = InputForm(
            self, "Service: ", (0, 0), init_str=service["service"]
        )
        self.username_form = InputForm(
            self, "Username: ", (1, 0), init_str=service["user"]
        )
        self.password_form = InputForm(
            self, "Password: ", (2, 0), init_str=service["password"],
        )
        self.notes_form = InputForm(
            self, "Notes: ", (3, 0), init_str=service["notes"]
        )
        self.text_fields = [
            self.service_form, self.username_form,
            self.password_form, self.notes_form
        ]
        self.running = True
        self.draw()
        service_name = self.service_form.get_input()
        if service_name is None:
            self.clear()
            return
        if service_name == "":
            self.console.msgbox.error("Service name cannot be empty")
            self.clear()
            return
        username = self.username_form.get_input()
        if username is None:
            self.clear()
            return
        password = self.password_form.get_input()
        if password is None:
            self.clear()
            return
        notes = self.notes_form.get_input()
        if notes is None:
            self.clear()
            return
        self.console.vault.update(
            service["id"], service_name, username, password, notes
        )
        self.console.msgbox.info("Service updated")
        self.clear()


class ShowServiceWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Service")

    def run(self, service):
        self.running = True
        self.draw_box()
        self.widget.addstr(0, 0, f"Service: {service['service']}")
        self.widget.addstr(1, 0, f"Username: {service['user']}")
        self.widget.addstr(2, 0, f"Password: {service['password']}")
        self.widget.addstr(3, 0, f"Notes: {service['notes']}")
        self.widget.addstr(8, 0, "Press any key to close")
        self.widget.getkey()
        self.clear()


async def run(screen, ws):
    app = Console(ws, screen)
    await app.run()
