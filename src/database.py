import sqlite3
from os import remove, path
import websockets

class Database:
    def __init__(self, database_name: str) -> None:
        self.database_name = database_name
        self.connection = sqlite3.connect(self.database_name)
        self.cursor = self.connection.cursor()
        
    def __del__(self) -> None:
        if self.connection:
            self.connection.close()
    
    def rm(self) -> None:
        self.connection.close()
        remove(self.database_name)
    
    def close(self) -> None:
        self.connection.close()
    
    def open(self) -> None:
        self.connection = sqlite3.connect(self.database_name)
        self.cursor = self.connection.cursor()
        
    def commit(self) -> None:
        self.connection.commit()
    
    def rollback(self) -> None:
        self.connection.rollback()
    
    def database_exists(self) -> bool:
        return path.exists(self.database_name)

    def add_users_table(self) -> None:
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    encrypted_symmetrical_key BYTES NOT NULL
            )"""
        )
        
    def add_services_table(self) -> None:
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS services(
                    service_id INTEGER PRIMARY KEY,
                    service TEXT,
                    username TEXT,
                    encrypted_password BYTES,
                    notes TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id)
            )"""
        )

    def table_exists(self, table_name: str) -> bool:
        self.cursor.execute(
            f"SELECT name FROM sqlite_master "
            f"WHERE type='table' AND name='{table_name}'"
        )
        return self.cursor.fetchone()

    def add_user(
        self, username: str, password_hash: str,
        encrypted_symmetrical_key: bytes
    ) -> None:
        self.cursor.execute(
            f"INSERT INTO users"
            f"(username, password_hash, encrypted_symmetrical_key)"
            f"VALUES (?, ?, ?)", (
                username, password_hash, encrypted_symmetrical_key
            )
        )
        
    def add_service(
        self, service: str, username: str, encrypted_password: bytes,
        notes: str = "", user_id: int = 0
    ) -> None:
        self.cursor.execute(
            f"INSERT INTO services"
            f"(service, username, encrypted_password, notes, user_id)"
            f"VALUES (?, ?, ?, ?, ?)", (
                service, username, encrypted_password, notes, user_id
            )
        )

    def delete_service(self, service_id: int) -> None:
        self.cursor.execute(
            f"DELETE FROM services WHERE service_id = ?", (service_id,)
        )
        
    def delete_user(self, username: str) -> None:
        self.cursor.execute(
            f"DELETE FROM users WHERE username = ?", (username,)
        )

    def find_user(self, username: str) -> dict:
        self.cursor.execute(
            f"SELECT * FROM users WHERE username = ?", (username,)
        )
        user = self.cursor.fetchone()
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "password_hash": user[2]
            }
        else:
            return {}
    
    def find_user_services(self, username: str) -> list:
        user = self.find_user(username)
        if user:
            self.cursor.execute(
                f"SELECT * FROM services WHERE user_id = ?", (user["id"],)
            )
            services = self.cursor.fetchall()
            services_list = []
            for service in services:
                services_list.append({
                    "service_id": service[0], "service": service[1],
                    "username": service[2], "encrypted_password": service[3],
                    "notes": service[4], "user_id": service[5]
                })
            return services_list
        else:
            return []
    
    def search_user_services(self, username: str, service_name: str) -> list:
        user = self.find_user(username)
        if user:
            service_name = f"%{service_name}%"
            self.cursor.execute(
                f"SELECT * FROM services "
                f"WHERE user_id = ? AND service LIKE ?", 
                (user["id"], service_name)
            )
            services = self.cursor.fetchall()
            if services:
                services_list = []
                for service in services:
                    services_list.append({
                        "service_id": service[0],
                        "service": service[1],
                        "username": service[2],
                        "encrypted_password": service[3],
                        "notes": service[4],
                        "user_id": service[5]
                    })
                return services_list
        return []
    
    def find_service(self, service_id: int) -> dict:
        self.cursor.execute(
            f"SELECT * FROM services WHERE service_id = ?", (service_id,)
        )
        service = self.cursor.fetchone()
        if service:
            return {
                "service_id": service[0], "service": service[1],
                "username": service[2], "encrypted_password": service[3],
                "notes": service[4], "user_id": service[5]
            }
        else:
            return {}
    
    def update_user_username(self, username: str, new_username: str) -> None:
        self.cursor.execute(
            f"UPDATE users SET username = ? WHERE username = ?",
            (new_username, username)
        )
    
    def update_user_password(self, username: str, password_hash: str) -> None:
        self.cursor.execute(
            f"UPDATE users SET password_hash = ? WHERE username = ?",
            (password_hash, username)
        )
    
    def update_service(
        self, service_id: int, service: str, username: str,
        encrypted_password: bytes, notes: str, user_id: int
    ) -> None:
        self.cursor.execute(
            f"UPDATE services SET service = ?, username = ?,"
            f"encrypted_password = ?, notes = ?"
            f"WHERE service_id = ? AND user_id = ?",
            (service, username, encrypted_password, notes, service_id, user_id)
        )
    
    def count_table(self, table_name: str) -> int:
        self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return self.cursor.fetchone()[0]
