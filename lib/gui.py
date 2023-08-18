import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as msg
from pyperclip import copy
from lib import encryption, utils
from os import name as os_name
from PIL import Image, ImageTk

class GUI:
    def __init__(self, database, icon):
        self.database = database
        self.root = tk.Tk()
        self.root.title("My GUI")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.login_widgets()
        self.ekstra_window = False
        self.icon = ImageTk.PhotoImage(Image.open(icon))
        self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)
    
    def on_closing(self):
        if msg.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()
    
    def login_widgets(self):
        self.login_frame = ttk.Frame(self.root, padding=10)
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        
        self.login_username_label = ttk.Label(self.login_frame, text="Username:")
        self.login_username_label.pack(pady=2)
        self.login_username = ttk.Entry(self.login_frame, width=30)
        self.login_username.pack(pady=10)
        self.login_username.focus()
        
        self.login_password_label = ttk.Label(self.login_frame, text="Password:")
        self.login_password_label.pack(pady=2)
        self.login_password = ttk.Entry(self.login_frame, width=30, show="*")
        self.login_password.pack(pady=10)
        
        self.login_button = ttk.Button(self.login_frame, text="Login", command=self.login)
        self.login_button.pack(pady=10)
        self.login_password.bind("<Return>", self.login_event)
        
        self.create_user_button = ttk.Button(self.login_frame, text="Create User", command=self.create_user_window)
        self.create_user_button.pack(pady=10)
    
    def main_page_widgets(self):
        self.main_page_frame = ttk.Frame(self.root, padding=10)
        self.main_page_frame.pack(fill=tk.BOTH, expand=True)
        
        self.main_page_username_label = ttk.Label(self.main_page_frame, text=f"Welcome {self.login_username.get()}")
        self.main_page_username_label.pack(pady=10)
        
        self.add_new_entry_button = ttk.Button(self.main_page_frame, text="Add New Entry", command=self.add_new_entry)
        self.add_new_entry_button.pack(pady=10)
        
        self.search_bar_label = ttk.Label(self.main_page_frame, text="Search:")
        self.search_bar_label.pack(pady=2)
        self.search_bar = ttk.Entry(self.main_page_frame, width=30)
        self.search_bar.pack(pady=2)
        self.search_bar.focus()
        
        self.table_wrapper = ttk.Frame(self.main_page_frame)
        self.table_wrapper.pack(pady=10)
        
        self.table_scrollbary = ttk.Scrollbar(self.table_wrapper, orient=tk.VERTICAL)
        self.table_scrollbary.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.table_scrollbarx = ttk.Scrollbar(self.table_wrapper, orient=tk.HORIZONTAL)
        self.table_scrollbarx.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.main_page_table = ttk.Treeview(self.table_wrapper, columns=("Service", "Username", "Password", "Notes"), yscrollcommand=self.table_scrollbary.set, xscrollcommand=self.table_scrollbarx.set, selectmode="browse")
        self.table_scrollbary.configure(command=self.main_page_table.yview)
        self.table_scrollbarx.configure(command=self.main_page_table.xview)
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
        self.main_page_table.bind("<Double-1>", self.open_edit_entry_window)
        # copy password to clipboard on right click
        self.main_page_table.bind("<Button-3>", self.copy_password)
        
        self.main_page_logout_button = ttk.Button(self.main_page_frame, text="Logout", command=self.logout)
        self.main_page_logout_button.pack(pady=10)
    
    def add_new_entry_window(self):
        self.ekstra_window = True
        self.new_entry_window = tk.Toplevel(self.root)
        self.new_entry_window.title("Add New Entry")
        self.new_entry_window.geometry("300x300")
        self.new_entry_window.resizable(False, False)
        self.new_entry_window.protocol("WM_DELETE_WINDOW", self.close_add_new_entry_window)
        self.new_entry_window.tk.call('wm', 'iconphoto', self.new_entry_window._w, self.icon)
        
        self.add_new_entry_frame = ttk.Frame(self.new_entry_window, padding=5)
        self.add_new_entry_frame.pack(fill=tk.BOTH, expand=True)
        
        self.new_service_label = ttk.Label(self.add_new_entry_frame, text="Service")
        self.new_service_label.pack(pady=2)
        self.new_service = ttk.Entry(self.add_new_entry_frame, width=30)
        self.new_service.pack(pady=2)
        self.new_service.focus()
        
        self.new_username_label = ttk.Label(self.add_new_entry_frame, text="Username")
        self.new_username_label.pack(pady=2)
        self.new_username = ttk.Entry(self.add_new_entry_frame, width=30)
        self.new_username.pack(pady=2)
        
        self.new_password_label = ttk.Label(self.add_new_entry_frame, text="Password")
        self.new_password_label.pack(pady=2)
        self.new_password = ttk.Entry(self.add_new_entry_frame, width=30)
        self.new_password.pack(pady=2)
        
        self.generate_password_button = ttk.Button(self.add_new_entry_frame, text="Generate Password", command=self.generate_password)
        self.generate_password_button.pack(pady=2)

        self.new_notes_label = ttk.Label(self.add_new_entry_frame, text="Notes")
        self.new_notes_label.pack(pady=2)
        self.new_notes = ttk.Entry(self.add_new_entry_frame, width=30)
        self.new_notes.pack(pady=2)
        
        self.add_button = ttk.Button(self.add_new_entry_frame, text="Add", command=self.add_entry)
        self.add_button.pack(pady=2)
        self.new_entry_window.bind("<Return>", self.add_entry_event)
    
    def create_user_window(self):
        self.ekstra_window = True
        self.create_new_user_window = tk.Toplevel(self.root)
        self.create_new_user_window.title("Create User")
        self.create_new_user_window.geometry("300x300")
        self.create_new_user_window.resizable(False, False)
        self.create_new_user_window.protocol("WM_DELETE_WINDOW", self.close_create_user_window)
        self.create_new_user_window.tk.call('wm', 'iconphoto', self.create_new_user_window._w, self.icon)
        
        self.create_user_frame = ttk.Frame(self.create_new_user_window, padding=5)
        self.create_user_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_username_label = ttk.Label(self.create_user_frame, text="Username")
        self.create_username_label.pack(pady=2)
        self.create_username = ttk.Entry(self.create_user_frame, width=30)
        self.create_username.pack(pady=2)
        self.create_username.focus()
        
        self.create_password_label = ttk.Label(self.create_user_frame, text="Password")
        self.create_password_label.pack(pady=2)
        self.create_password = ttk.Entry(self.create_user_frame, width=30)
        self.create_password.pack(pady=2)
        
        self.create_confirm_password_label = ttk.Label(self.create_user_frame, text="Confirm Password")
        self.create_confirm_password_label.pack(pady=2)
        self.create_confirm_password = ttk.Entry(self.create_user_frame, width=30)
        self.create_confirm_password.pack(pady=2)
        
        self.create_button = ttk.Button(self.create_user_frame, text="Create", command=self.create_user)
        self.create_button.pack(pady=2)
        self.create_new_user_window.bind("<Return>", self.create_user_event)
    
    def open_edit_entry_window(self, _):
        self.ekstra_window = True
        self.edit_entry_window = tk.Toplevel(self.root)
        self.edit_entry_window.title("Edit Entry")
        self.edit_entry_window.geometry("300x300")
        self.edit_entry_window.resizable(False, False)
        self.edit_entry_window.protocol("WM_DELETE_WINDOW", self.close_edit_entry_window)
        self.edit_service_id = self.main_page_table.item(self.main_page_table.focus())['text']
        edit_service = self.main_page_table.item(self.main_page_table.focus())['values'][0]
        edit_username = self.main_page_table.item(self.main_page_table.focus())['values'][1]
        edit_password = self.main_page_table.item(self.main_page_table.focus())['values'][2]
        edit_notes = self.main_page_table.item(self.main_page_table.focus())['values'][3]
        self.edit_entry_window.tk.call('wm', 'iconphoto', self.edit_entry_window._w, self.icon)
        
        self.edit_entry_frame = ttk.Frame(self.edit_entry_window, padding=5)
        self.edit_entry_frame.pack(fill=tk.BOTH, expand=True)
        
        self.edit_service_label = ttk.Label(self.edit_entry_frame, text=f"Editing {edit_service}")
        self.edit_service_label.pack(pady=2)
        self.edit_service = ttk.Entry(self.edit_entry_frame, width=30)
        self.edit_service.insert(0, edit_service)
        self.edit_service.pack(pady=2)
        self.edit_service.focus()
        
        self.edit_username_label = ttk.Label(self.edit_entry_frame, text="Username")
        self.edit_username_label.pack(pady=2)
        self.edit_username = ttk.Entry(self.edit_entry_frame, width=30)
        self.edit_username.insert(0, edit_username)
        self.edit_username.pack(pady=2)
        
        self.edit_password_label = ttk.Label(self.edit_entry_frame, text="Password")
        self.edit_password_label.pack(pady=2)
        self.edit_password = ttk.Entry(self.edit_entry_frame, width=30)
        self.edit_password.insert(0, edit_password)
        self.edit_password.pack(pady=2)
        
        self.edit_generate_password_button = ttk.Button(self.edit_entry_frame, text="Generate Password", command=self.generate_edit_password)
        self.edit_generate_password_button.pack(pady=2)
        
        self.edit_notes_label = ttk.Label(self.edit_entry_frame, text="Notes")
        self.edit_notes_label.pack(pady=2)
        self.edit_notes = ttk.Entry(self.edit_entry_frame, width=30)
        self.edit_notes.insert(0, edit_notes)
        self.edit_notes.pack(pady=2)
        
        self.edit_button = ttk.Button(self.edit_entry_frame, text="Edit", command=self.edit_entry)
        self.edit_button.pack(pady=2)
        self.edit_entry_window.bind("<Return>", self.edit_entry_event)
        
        self.edit_delete_button = ttk.Button(self.edit_entry_frame, text="Delete", command=self.delete_entry)
        self.edit_delete_button.pack(pady=2)
    
    def login(self):
        current_user = self.database.find_user(self.login_username.get())
        current_username = current_user["username"]
        current_user_id = current_user["id"]
        current_password = current_user["password_hash"]
        if encryption.verify_password(self.login_password.get(), current_password):
            if self.ekstra_window:
                self.close_create_user_window()
            print(f"{current_username} logged in")
            print(f"User ID: {current_user_id}")
            self.login_frame.forget()
            self.main_page_widgets()
    
    def logout(self):
        if self.ekstra_window:
            self.close_add_new_entry_window()
            self.close_edit_entry_window()
        print(f"{self.login_username.get()} logged out")
        self.main_page_frame.forget()
        self.login_widgets()
    
    def add_new_entry(self):
        self.add_new_entry_window()
        
    def add_entry(self):
        encrypted_symmetrical_key = self.database.find_user(self.login_username.get())["encrypted_symmetrical_key"]
        symmetrical_key = encryption.decrypt_symmetrical_key(encrypted_symmetrical_key)
        encrypted_password = encryption.encrypt_password(self.new_password.get(), symmetrical_key)
        
        user_id = self.database.find_user(self.login_username.get())["id"]
        self.database.add_service(self.new_service.get(), self.new_username.get(), encrypted_password, self.new_notes.get(), user_id=user_id)
        self.database.commit()
        print("new entry added")
        
        self.main_page_table.delete(*self.main_page_table.get_children())
        self.fill_table()
        self.close_add_new_entry_window()
    
    def close_add_new_entry_window(self):
        self.new_entry_window.destroy()
        self.ekstra_window = False
        
    def close_create_user_window(self):
        self.create_new_user_window.destroy()
        self.ekstra_window = False
        
    def close_edit_entry_window(self):
        self.edit_entry_window.destroy()
        self.ekstra_window = False
        
    def generate_password(self):
        self.new_password.delete(0, tk.END)
        self.new_password.insert(0, utils.generate_password(16))
    
    def generate_edit_password(self):
        self.edit_password.delete(0, tk.END)
        self.edit_password.insert(0, utils.generate_password(16))
    
    def create_user(self):
        username = self.create_username.get()
        password = self.create_password.get()
        confirm_password = self.create_confirm_password.get()
        if password == confirm_password:
            password_hash = encryption.hash_password(password)
            symmetrical_key = encryption.generate_symmetrical_key(password)
            encrypted_symmetrical_key = encryption.encrypt_symmetrical_key(symmetrical_key)
            self.database.add_user(username, password_hash, encrypted_symmetrical_key)
            self.database.commit()
            print("user created")
            self.close_create_user_window()
        else:
            print("passwords do not match")
    
    def fill_table(self, search=None):
        self.main_page_table.delete(*self.main_page_table.get_children())
        current_user = self.login_username.get()
        search = self.search_bar.get()
        if search:
            self.main_page_table.delete(*self.main_page_table.get_children())
            services = self.database.search_user_services(current_user, search)
        else:
            services = self.database.find_user_services(current_user)
        for service in services:
            encrypted_symmetrical_key = self.database.find_user(current_user)["encrypted_symmetrical_key"]
            symmetrical_key = encryption.decrypt_symmetrical_key(encrypted_symmetrical_key)
            service["decrypted_password"] = encryption.decrypt_password(service["encrypted_password"], symmetrical_key)
            self.main_page_table.insert("", "end", text=service["service_id"], values=(service["service"], service["username"], service["decrypted_password"], service["notes"]))
        
    def edit_entry(self):
        current_user = self.database.find_user(self.login_username.get())
        encrypted_symmetrical_key = current_user["encrypted_symmetrical_key"]
        user_id = current_user["id"]
        
        symmetrical_key = encryption.decrypt_symmetrical_key(encrypted_symmetrical_key)
        encrypted_password = encryption.encrypt_password(self.edit_password.get(), symmetrical_key)
        
        self.database.update_service(self.edit_service_id, self.edit_service.get(), self.edit_username.get(), encrypted_password, self.edit_notes.get(), user_id)
        if msg.askokcancel("Edit", "Are you sure you want to edit this entry?"):
            self.database.commit()
            print("entry edited")
        else:
            print("entry not edited")
            self.database.rollback()
        
        self.main_page_table.delete(*self.main_page_table.get_children())
        self.fill_table()
        self.close_edit_entry_window()
    
    def delete_entry(self):
        self.database.delete_service(self.edit_service_id)
        self.database.commit()
        print("entry deleted")
        
        self.main_page_table.delete(*self.main_page_table.get_children())
        self.fill_table()
        self.close_edit_entry_window()
    
    def copy_password(self, _):
        copy(self.main_page_table.item(self.main_page_table.focus())['values'][2])
        print("password copied to clipboard")
    
    def login_event(self, _):
        self.login()
    
    def create_user_event(self, _):
        self.create_user()
    
    def add_entry_event(self, _):
        self.add_entry()
    
    def edit_entry_event(self, _):
        self.edit_entry()
