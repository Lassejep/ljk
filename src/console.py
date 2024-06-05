import pyperclip
import traceback
import curses
from curses import textpad
import sys
import re
from . import client
from .encryption import generate_password


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
        self.vault_window = VaultWindow(self)
        self.services_window = ServiceWindow(self)

    async def run(self):
        self.running = True
        while self.running:
            self.start_menu.run()
            await self.start_select()

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
        self.msgbox.keypad(True)
        self.title = "Messages"
        self.error_color = self.console.error_color

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

    def clear(self):
        self.box.erase()
        self.box.refresh()
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

    def navigate(self):
        key = self.menu.getkey()
        if key == "k" or key == "KEY_UP":
            self.pos = ((self.pos[0] - 1) % len(self.options), self.pos[1])
        if key == "j" or key == "KEY_DOWN":
            self.pos = ((self.pos[0] + 1) % len(self.options), self.pos[1])
        if key == "\n":
            self.running = False
        if self.console.escape(key):
            self.running = False
        self.draw()


class StartMenu(Menu):
    def __init__(self, console):
        super().__init__(console, "Start Menu")
        self.options = ["1. Login", "2. Register", "3. Exit"]

    def run(self):
        self.running = True
        self.menu.erase()
        while self.running:
            self.draw()
            self.navigate()
            self.menu.erase()


class MainMenu(Menu):
    def __init__(self, console):
        super().__init__(console, title="Main Menu")
        self.options = [
            "1. Services", "2. Vaults", "3. Settings", "4. Logout", "5. Exit"
        ]

    def run(self):
        self.running = True
        self.menu.erase()
        curses.curs_set(0)
        while self.running:
            self.draw()
            self.navigate()
            self.menu.erase()

    def select(self):
        if self.pos[0] == 0:
            pass
        if self.pos[0] == 1:
            pass
        if self.pos[0] == 2:
            pass
        if self.pos[0] == 3:
            pass
        if self.pos[0] == 4:
            self.running = False


class Window:
    def __init__(self, console, title="Window"):
        self.console = console
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

    def draw(self):
        self.draw_box()
        self.draw_keybinds()
        self.draw_options()
        self.window.refresh()

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
                        i + self.y_offset, 1, option, curses.A_REVERSE
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
                window.addstr(y_offset, x_offset + 2, col, curses.A_REVERSE)
                window.vline(y_offset, x_offset + length, curses.ACS_VLINE, 1)
            else:
                window.addstr(y_offset, x_offset + 1, col)
                window.vline(y_offset, x_offset + length, curses.ACS_VLINE, 1)
            x_offset += length

    def navigate(self):
        key = self.window.getkey()
        if key == "k" or key == "KEY_UP":
            self.pos = ((self.pos[0] - 1) % len(self.options), self.pos[1])
        if key == "j" or key == "KEY_DOWN":
            self.pos = ((self.pos[0] + 1) % len(self.options), self.pos[1])
        if key == "\n":
            self.running = False
        if self.escape(key):
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


class VaultWindow(Window):
    def __init__(self, console):
        super().__init__(console, "Vaults")
        self.keybinds = [
            "<Enter> Select vault", "<A> Add vault",
            "<D> Delete vault", "<R> Rename vault", "<ESC> Main menu"
        ]

    def run(self):
        self.running = True
        self.window.erase()
        while self.running:
            self.draw()
            self.navigate()
            self.window.erase()

    def select(self):
        if self.pos[0] == 0:
            pass
        if self.pos[0] == 1:
            pass
        if self.pos[0] == 2:
            pass
        if self.pos[0] == 3:
            pass
        if self.pos[0] == 4:
            self.running = False


class SettingsWindow(Window):
    def __init__(self, console):
        super().__init__(console, "Settings")
        self.options = [
            "1. Change master password", "2. Change email",
            "3. Delete account"
        ]

    def run(self):
        self.running = True
        self.window.erase()
        while self.running:
            self.draw()
            self.navigate()
            self.window.erase()


class ServiceWindow(Window):
    def __init__(self, console):
        super().__init__(console, "Services")
        self.keybinds = [
            "<Y> Copy password", "<Enter> Show service",
            "<A> Add service", "<D> Delete service",
            "<E> Edit service", "<ESC> Main menu"
        ]

    def run(self):
        self.running = True
        self.window.erase()
        while self.running:
            self.draw()
            self.navigate()
            self.window.erase()

    def select(self):
        if self.pos[0] == 0:
            pass
        if self.pos[0] == 1:
            pass
        if self.pos[0] == 2:
            pass
        if self.pos[0] == 3:
            pass
        if self.pos[0] == 4:
            pass
        if self.pos[0] == 5:
            self.running = False


class InputForm:
    def __init__(
        self, widget, prompt, pos, init_str="", secret=False, height=1
    ):
        self.widget = widget
        self.widget_size = widget.getmaxyx()
        self.prompt = prompt
        self.init_str = init_str
        self.height = height
        self.secret = secret
        self.pos = pos
        loc = self.widget.getbegyx()
        self.input_field = self.widget.subpad(
            self.height, self.widget_size[1] - len(self.prompt),
            loc[0] + self.pos[0], loc[1] + self.pos[1] + len(self.prompt)
        )
        self.textbox = textpad.Textbox(self.input_field, insert_mode=True)
        self.background_color = curses.color_pair(1)

    def draw(self):
        self.widget.addstr(self.pos[0], self.pos[1], self.prompt)
        if self.secret:
            self.input_field.attron(self.background_color)
        self.input_field.addstr(0, 0, self.init_str)
        self.input_field.refresh()

    def validate(self, key):
        if key == 27:
            self.running = False
            return 7
        if key == 10:
            return 7
        return key

    def get_input(self):
        self.input_field.move(0, len(self.init_str))
        curses.curs_set(1)
        out = self.textbox.edit(self.validate)
        curses.curs_set(0)
        return out


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
        for text_field in self.text_fields:
            text_field.input_field.erase()
            text_field.input_field.refresh()
        self.widget.erase()
        self.widget.refresh()


class LoginWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Login")
        self.console = console
        self.email_form = InputForm(self.widget, "Email: ", (0, 0))
        self.mpass_form = InputForm(
            self.widget, "Master password: ", (1, 0), secret=True
        )
        self.text_fields = [self.email_form, self.mpass_form]

    async def run(self):
        self.running = True
        self.draw()
        email = self.email_form.get_input()
        if len(email) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return None
        mpass = self.mpass_form.get_input()
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
        return user


class RegisterWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Register")
        self.email_form = InputForm(self.widget, "Email: ", (0, 0))
        self.mpass_form = InputForm(
            self.widget, "Master password: ", (1, 0), secret=True
        )
        self.repeat_mpass_form = InputForm(
            self.widget, "Repeat master password: ", (2, 0), secret=True
        )
        self.text_fields = [
            self.email_form, self.mpass_form, self.repeat_mpass_form
        ]

    async def run(self):
        self.running = True
        self.draw()
        email = self.email_form.get_input()
        if len(email) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return
        mpass = self.mpass_form.get_input()
        if len(mpass) < 8:
            self.console.msgbox.error("Must be at least 8 characters long")
            self.clear()
            return
        repeat_mpass = self.repeat_mpass_form.get_input()
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


class AddVaultWidget(Widget):
    def __init__(self, console):
        super().__init__(console, "Add vault")
        self.vault_name_form = InputForm(self.widget, "Vault name: ", (0, 0))
        self.text_fields = [self.vault_name_form]

    async def run(self):
        self.running = True
        self.draw()
        vault_name = self.vault_name_form.get_input()
        if vault_name == "":
            self.clear()
            return
        if not await client.create_vault(self.console.ws, vault_name):
            self.console.msgbox.error("Failed to create vault")
            self.clear()
            return
        self.console.msgbox.info("Vault created")
        self.clear()


async def run(screen, ws):
    app = Console(ws, screen)
    await app.run()
