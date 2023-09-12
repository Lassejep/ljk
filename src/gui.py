import asyncio
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as msg
from pyperclip import copy
from PIL import Image, ImageTk
from src import encryption, events

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.login_widgets()
        self.vault = None
        self.ekstra_window = None
        self.loop = asyncio.get_event_loop()

        self.icon_path = "img/ljk.gif"
        self.icon = ImageTk.PhotoImage(Image.open(self.icon_path))
        self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)
    
    def on_closing(self):
        if msg.askokcancel("Quit", "Do you want to quit?"):
            if self.vault is not None:
                self.logout()
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()
    
    def login_widgets(self):
        self.login_frame = ttk.Frame(self.root, padding=10)
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        
        email_label = ttk.Label(
            self.login_frame, text="Email:"
        )
        email_label.pack(pady=2)
        self.master_email = ttk.Entry(self.login_frame, width=30)
        self.master_email.pack(pady=10)
        self.master_email.focus()
        
        master_password_label = ttk.Label(
            self.login_frame, text="Master Password:"
        )
        master_password_label.pack(pady=2)
        self.master_password = ttk.Entry(self.login_frame, width=30, show="*")
        self.master_password.pack(pady=10)
        
        login_button = ttk.Button(
            self.login_frame, text="Login", command=self.login
        )
        login_button.pack(pady=10)
        login_button.bind("<Return>", self.login_event)
        self.master_email.bind("<Return>", self.login_event)
        self.master_password.bind("<Return>", self.login_event)
        
        create_user_button = ttk.Button(
            self.login_frame, text="Create User",
            command=self.create_user_window
        )
        create_user_button.pack(pady=10)
    
    def main_page_widgets(self):
        self.main_page_frame = ttk.Frame(self.root, padding=10)
        self.main_page_frame.pack(fill=tk.BOTH, expand=True)
        
        main_page_email_label = ttk.Label(
            self.main_page_frame, text=f"Welcome {self.master_email.get()}"
        )
        main_page_email_label.pack(pady=10)
        
        add_new_service_button = ttk.Button(
            self.main_page_frame, text="Add New Entry",
            command=self.add_new_service
        )
        add_new_service_button.pack(pady=10)
        
        search_bar_label = ttk.Label(self.main_page_frame, text="Search:")
        search_bar_label.pack(pady=2)
        self.search_bar = ttk.Entry(self.main_page_frame, width=30)
        self.search_bar.pack(pady=2)
        self.search_bar.focus()
        
        table_wrapper = ttk.Frame(self.main_page_frame)
        table_wrapper.pack(pady=10)
        
        table_scrollbary = ttk.Scrollbar(
            table_wrapper, orient=tk.VERTICAL
        )
        table_scrollbary.pack(side=tk.RIGHT, fill=tk.Y)
        
        table_scrollbarx = ttk.Scrollbar(
            table_wrapper, orient=tk.HORIZONTAL
        )
        table_scrollbarx.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.main_page_table = ttk.Treeview(
            table_wrapper,
            columns=("Service", "Username", "Password", "Notes"),
            yscrollcommand=table_scrollbary.set,
            xscrollcommand=table_scrollbarx.set,
            selectmode="browse"
        )
        table_scrollbary.configure(command=self.main_page_table.yview)
        table_scrollbarx.configure(command=self.main_page_table.xview)
        self.main_page_table.heading("#0", text="ID")
        self.main_page_table.heading("#1", text="Service")
        self.main_page_table.heading("#2", text="Username")
        self.main_page_table.heading("#3", text="Password")
        self.main_page_table.heading("#4", text="Notes")
        self.main_page_table.column("#0", width=50)
        self.main_page_table.column("#1", width=200)
        self.main_page_table.column("#2", width=100)
        self.main_page_table.column("#3", width=100)
        self.main_page_table.column("#4", width=100)
        self.main_page_table.pack()
        self.fill_table()
        
        self.search_bar.bind("<KeyRelease>", self.fill_table)
        self.main_page_table.bind("<Double-1>", self.open_edit_service_window)
        self.main_page_table.bind("<Button-3>", self.copy_password)
        
        main_page_logout_button = ttk.Button(
            self.main_page_frame, text="Logout", command=self.logout
        )
        main_page_logout_button.pack(pady=10)
    
    def add_new_service_window(self):
        self.new_service_window = tk.Toplevel(self.root)
        self.ekstra_window = self.new_service_window
        self.new_service_window.title("Add New Entry")
        self.new_service_window.geometry("300x300")
        self.new_service_window.resizable(False, False)
        self.new_service_window.protocol(
            "WM_DELETE_WINDOW", self.close_ekstra_window
        )
        self.new_service_window.tk.call(
            'wm', 'iconphoto', self.new_service_window._w, self.icon
        )
        
        self.add_new_service_frame = ttk.Frame(
            self.new_service_window, padding=5
        )
        self.add_new_service_frame.pack(fill=tk.BOTH, expand=True)
        
        new_service_label = ttk.Label(
            self.add_new_service_frame, text="Service"
        )
        new_service_label.pack(pady=2)
        self.new_service = ttk.Entry(self.add_new_service_frame, width=30)
        self.new_service.pack(pady=2)
        self.new_service.focus()
        
        new_username_label = ttk.Label(
            self.add_new_service_frame, text="Username"
        )
        new_username_label.pack(pady=2)
        self.new_username = ttk.Entry(self.add_new_service_frame, width=30)
        self.new_username.pack(pady=2)
        
        new_password_label = ttk.Label(
            self.add_new_service_frame, text="Password"
        )
        new_password_label.pack(pady=2)
        self.new_password = ttk.Entry(self.add_new_service_frame, width=30)
        self.new_password.pack(pady=2)
        
        self.generate_password_button = ttk.Button(
            self.add_new_service_frame, text="Generate Password",
            command=self.generate_password
        )
        self.generate_password_button.pack(pady=2)

        new_notes_label = ttk.Label(
            self.add_new_service_frame, text="Notes"
        )
        new_notes_label.pack(pady=2)
        self.new_notes = ttk.Entry(self.add_new_service_frame, width=30)
        self.new_notes.pack(pady=2)
        
        self.add_button = ttk.Button(
            self.add_new_service_frame, text="Add", command=self.add_service
        )
        self.add_button.pack(pady=2)
        self.new_service_window.bind("<Return>", self.add_service_event)
    
    def create_user_window(self):
        self.create_new_user_window = tk.Toplevel(self.root)
        self.ekstra_window = self.create_new_user_window
        self.create_new_user_window.title("Create User")
        self.create_new_user_window.geometry("300x300")
        self.create_new_user_window.resizable(False, False)
        self.create_new_user_window.protocol(
            "WM_DELETE_WINDOW", self.close_ekstra_window
        )
        self.create_new_user_window.tk.call(
            'wm', 'iconphoto', self.create_new_user_window._w, self.icon
        )
        
        self.create_user_frame = ttk.Frame(
            self.create_new_user_window, padding=5
        )
        self.create_user_frame.pack(fill=tk.BOTH, expand=True)
        
        create_email_label = ttk.Label(
            self.create_user_frame, text="Email"
        )
        create_email_label.pack(pady=2)
        self.create_email = ttk.Entry(self.create_user_frame, width=30)
        self.create_email.pack(pady=2)
        self.create_email.focus()
        
        create_password_label = ttk.Label(
            self.create_user_frame, text="Master Password"
        )
        create_password_label.pack(pady=2)
        self.create_password = ttk.Entry(
            self.create_user_frame, width=30, show="*"
        )
        self.create_password.pack(pady=2)
        
        create_confirm_master_password_label = ttk.Label(
            self.create_user_frame, text="Confirm Master Password"
        )
        create_confirm_master_password_label.pack(pady=2)
        self.create_confirm_master_password = ttk.Entry(
            self.create_user_frame, width=30, show="*"
        )
        self.create_confirm_master_password.pack(pady=2)
        
        self.create_button = ttk.Button(
            self.create_user_frame, text="Create", command=self.create_user
        )
        self.create_button.pack(pady=2)
        self.create_new_user_window.bind("<Return>", self.create_user_event)
    
    def open_edit_service_window(self, _):
        self.edit_service_window = tk.Toplevel(self.root)
        self.ekstra_window = self.edit_service_window
        self.edit_service_window.title("Edit Entry")
        self.edit_service_window.geometry("300x300")
        self.edit_service_window.resizable(False, False)
        self.edit_service_window.protocol(
            "WM_DELETE_WINDOW", self.close_ekstra_window
        )
        self.edit_service_id = self.main_page_table.item(
            self.main_page_table.focus()
        )['text']
        edit_service = self.main_page_table.item(
            self.main_page_table.focus()
        )['values'][0]
        edit_username = self.main_page_table.item(
            self.main_page_table.focus()
        )['values'][1]
        edit_password = self.main_page_table.item(
            self.main_page_table.focus()
        )['values'][2]
        edit_notes = self.main_page_table.item(
            self.main_page_table.focus()
        )['values'][3]
        self.edit_service_window.tk.call(
            'wm', 'iconphoto', self.edit_service_window._w, self.icon
        )
        
        self.edit_service_frame = ttk.Frame(self.edit_service_window, padding=5)
        self.edit_service_frame.pack(fill=tk.BOTH, expand=True)
        
        edit_service_label = ttk.Label(
            self.edit_service_frame, text=f"Editing {edit_service}"
        )
        edit_service_label.pack(pady=2)
        self.edit_service = ttk.Entry(self.edit_service_frame, width=30)
        self.edit_service.insert(0, edit_service)
        self.edit_service.pack(pady=2)
        self.edit_service.focus()
        
        edit_username_label = ttk.Label(
            self.edit_service_frame, text="Username"
        )
        edit_username_label.pack(pady=2)
        self.edit_username = ttk.Entry(self.edit_service_frame, width=30)
        self.edit_username.insert(0, edit_username)
        self.edit_username.pack(pady=2)
        
        edit_password_label = ttk.Label(
            self.edit_service_frame, text="Password"
        )
        edit_password_label.pack(pady=2)
        self.edit_password = ttk.Entry(self.edit_service_frame, width=30)
        self.edit_password.insert(0, edit_password)
        self.edit_password.pack(pady=2)
        
        self.edit_generate_password_button = ttk.Button(
            self.edit_service_frame, text="Generate Password",
            command=self.generate_password
        )
        self.edit_generate_password_button.pack(pady=2)
        
        edit_notes_label = ttk.Label(self.edit_service_frame, text="Notes")
        edit_notes_label.pack(pady=2)
        self.edit_notes = ttk.Entry(self.edit_service_frame, width=30)
        self.edit_notes.insert(0, edit_notes)
        self.edit_notes.pack(pady=2)
        
        self.edit_button = ttk.Button(
            self.edit_service_frame, text="Edit", command=self.edit_service
        )
        self.edit_button.pack(pady=2)
        self.edit_service_window.bind("<Return>", self.edit_service_event)
        
        self.edit_delete_button = ttk.Button(
            self.edit_service_frame, text="Delete", command=self.delete_service
        )
        self.edit_delete_button.pack(pady=2)
    
    def login(self):
        if self.ekstra_window is not None:
            self.close_ekstra_window()

        if self.loop.run_until_complete(events.verify_user(
            self.master_email.get(), self.master_password.get()
        )):
            print(f"{self.master_email.get()} logged in")
            self.vault = self.loop.run_until_complete(
                events.get_vault(
                    self.master_email.get(),
                    self.master_password.get()
                )
            )
            self.login_frame.forget()
            self.main_page_widgets()
            self.root.title("LJKey")
        else:
            raise Exception("Invalid email or password")
    
    def logout(self):
        if self.ekstra_window is not None:
            self.close_ekstra_window()
        self.vault.commit()
        self.loop.run_until_complete(events.update_vault(
            self.master_email.get(),
            self.master_password.get(),
            self.vault
        ))
        self.vault.rm()
        self.vault = None
        print(f"{self.master_email.get()} logged out")
        self.main_page_frame.forget()
        self.login_widgets()
        self.root.title("Login")
    
    def add_new_service(self):
        self.add_new_service_window()
        
    def add_service(self):
        self.vault.add_service(
            self.new_service.get(), self.new_username.get(),
            self.new_password.get(), self.new_notes.get()
        )
        self.vault.commit()
        self.loop.run_until_complete(events.update_vault(
            self.master_email.get(), self.master_password.get(), self.vault
        ))
        print("new service added")
        
        self.main_page_table.delete(*self.main_page_table.get_children())
        self.fill_table()
        self.close_ekstra_window()
    
    def close_ekstra_window(self):
        self.ekstra_window.destroy()
        self.ekstra_window = None

    def generate_password(self):
        self.new_password.delete(0, tk.END)
        self.new_password.insert(0, events.generate_password(16))
    
    def create_user(self):
        email = self.create_email.get()
        master_password = self.create_password.get()
        confirm_master_password = self.create_confirm_master_password.get()
        if master_password == confirm_master_password:
            reply = self.loop.run_until_complete(
                events.create_user(email, master_password)
            )
            self.close_ekstra_window()
        else:
            raise Exception("Passwords do not match")
    
    def fill_table(self, search=None):
        self.main_page_table.delete(*self.main_page_table.get_children())
        email = self.master_email.get()
        search = self.search_bar.get()
        if search:
            services = self.vault.search_services(search)
        else:
            services = self.vault.get_services()
        for service in services:
            self.main_page_table.insert(
                "", "end", text=service["service_id"],
                values=(
                    service["service"], service["username"],
                    service["password"], service["notes"]
                )
            )
        
    def edit_service(self):
        current_user = self.database.find_user(self.master_email.get())
        user_id = current_user["id"]
        
        encrypted_service_password = encryption.encrypt_password(
            self.edit_password.get()
        )
        
        self.database.update_service(
            self.edit_service_id, self.edit_service.get(),
            self.edit_username.get(), encrypted_service_password,
            self.edit_notes.get(), user_id
        )
        if msg.askokcancel(
            "Edit", "Are you sure you want to edit this service?"
        ):
            self.database.commit()
            print("service edited")
        else:
            print("service not edited")
            self.database.rollback()
        
        self.main_page_table.delete(*self.main_page_table.get_children())
        self.fill_table()
        self.close_ekstra_window()
    
    def delete_service(self):
        self.database.delete_service(self.edit_service_id)
        self.database.commit()
        print("service deleted")
        
        self.main_page_table.delete(*self.main_page_table.get_children())
        self.fill_table()
        self.close_ekstra_window()
    
    def copy_password(self, _):
        copy(self.main_page_table.item(
            self.main_page_table.focus()
        )['values'][2])
        print("password copied to clipboard")
    
    def login_event(self, _):
        self.login()
    
    def create_user_event(self, _):
        self.create_user()
    
    def add_service_event(self, _):
        self.add_service()
    
    def edit_service_event(self, _):
        self.edit_service()
