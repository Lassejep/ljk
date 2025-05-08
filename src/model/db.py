import sqlite3
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union


class Database:
    def __init__(self, database_name: str) -> None:
        self.database_name: str = database_name
        self.connection: sqlite3.Connection = sqlite3.connect(self.database_name)
        self.cursor: sqlite3.Cursor = self.connection.cursor()
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                auth_key BYTES NOT NULL
            )"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS vaults(
                id INTEGER PRIMARY KEY,
                uid INTEGER NOT NULL,
                name TEXT NOT NULL,
                key BYTES NOT NULL,
                data BLOB,
                FOREIGN KEY(uid) REFERENCES users(id)
            )"""
        )

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def close(self) -> None:
        self.connection.close()

    def add_user(self, email: str, auth_key: str) -> None:
        try:
            self.cursor.execute(
                """INSERT INTO users(
                    email, auth_key
                ) VALUES (?, ?)""",
                (email, auth_key),
            )
        except sqlite3.IntegrityError:
            raise Exception(f"User with email: {email} already exists")

    def delete_user(self, uid: int) -> None:
        try:
            self.cursor.execute("""DELETE FROM users WHERE id = ?""", (uid,))
        except sqlite3.IntegrityError:
            raise Exception(f"User with id: {uid} does not exist")

    def get_user(self, uid: int) -> Dict[str, Union[int, str, str]]:
        self.cursor.execute("""SELECT * FROM users WHERE id = ?""", (uid,))
        user = self.cursor.fetchone()
        if user is None:
            raise Exception(f"User with id: {uid} not found")
        return {
            "id": user[0],
            "email": user[1],
            "auth_key": user[2],
        }

    def update_email(self, uid: int, new_email: str, new_auth_key: str) -> None:
        try:
            self.cursor.execute(
                """UPDATE users SET email = ?, auth_key = ? WHERE id = ?""",
                (new_email, new_auth_key, uid),
            )
        except sqlite3.IntegrityError:
            raise Exception(f"User with email: {new_email} already exists")

    def update_auth_key(self, uid: int, auth_key: str) -> None:
        self.get_user(uid)
        self.cursor.execute(
            """UPDATE users SET auth_key = ? WHERE id = ?""", (auth_key, uid)
        )

    def get_id(self, email: str) -> int:
        self.cursor.execute("""SELECT id FROM users WHERE email = ?""", (email,))
        id = self.cursor.fetchone()
        if id is None:
            raise Exception(f"User with email: {email} not found")
        return id[0]

    def get_auth_key(self, uid: int) -> str:
        self.cursor.execute("""SELECT auth_key FROM users WHERE id = ?""", (uid,))
        auth_key = self.cursor.fetchone()
        if auth_key is None:
            raise Exception(f"User with id: {uid} not found")
        return auth_key[0]

    def add_vault(self, uid: int, name: str, key: str, data: str) -> None:
        if name.strip() == "":
            raise Exception("Vault name cannot be empty")
        try:
            self.cursor.execute(
                """INSERT INTO vaults(
                    uid, name, key, data
                ) VALUES (?, ?, ?, ?)""",
                (uid, name, key, data),
            )
        except sqlite3.IntegrityError:
            raise Exception(f"Vault with name: {name} already exists")

    def delete_vault(self, uid: int, name: str) -> None:
        try:
            self.cursor.execute(
                """DELETE FROM vaults WHERE uid = ? AND name = ?""", (uid, name)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"Vault with name: {name} does not exist")

    def get_vaults(self, uid: int) -> Dict[str, List[Union[int, int, str, str, str]]]:
        self.cursor.execute("""SELECT * FROM vaults WHERE uid = ?""", (uid,))
        vaults = self.cursor.fetchall()
        if len(vaults) <= 0:
            return None
        return [
            {
                "id": vault[0],
                "uid": vault[1],
                "name": vault[2],
                "key": vault[3],
                "data": vault[4],
            }
            for vault in vaults
        ]

    def get_vault(
        self, uid: int, name: str
    ) -> Dict[str, Union[int, int, str, str, str]]:
        self.cursor.execute(
            """SELECT * FROM vaults WHERE uid = ? AND name = ?""", (uid, name)
        )
        vault = self.cursor.fetchone()
        if vault is None:
            raise Exception(f"Vault with name: {name} not found")
        return {
            "id": vault[0],
            "uid": vault[1],
            "name": vault[2],
            "key": vault[3],
            "data": vault[4],
        }

    def get_vault_key(self, uid: int, name: str) -> str:
        vault = self.get_vault(uid, name)
        return vault["key"]

    def get_vault_data(self, uid: int, name: str) -> str:
        vault = self.get_vault(uid, name)
        return vault["data"]

    def get_vault_id(self, uid: int, name: str) -> int:
        vault = self.get_vault(uid, name)
        return vault["id"]

    def update_vault_name(self, uid: int, name: str, new_name: str) -> None:
        if new_name.strip() == "":
            raise Exception("Vault name cannot be empty")
        if name == new_name:
            return
        self.get_vault(uid, name)
        try:
            self.get_vault(uid, new_name)
            raise Exception(f"Vault with name: {new_name} already exists")
        except Exception:
            pass
        self.cursor.execute(
            """UPDATE vaults SET name = ? WHERE uid = ? AND name = ?""",
            (new_name, uid, name),
        )

    def update_vault_key(self, uid: int, name: str, key: str) -> None:
        if key.strip() == "":
            raise Exception("Vault key cannot be empty")
        if self.get_vault_key(uid, name) == key:
            return
        self.get_vault(uid, name)
        self.cursor.execute(
            """UPDATE vaults SET key = ? WHERE uid = ? AND name = ?""", (key, uid, name)
        )

    def update_vault(self, uid: int, name: str, data: str) -> None:
        if data.strip() == "":
            raise Exception("Vault data cannot be empty")
        if self.get_vault_data(uid, name) == data:
            return
        self.get_vault(uid, name)
        self.cursor.execute(
            """UPDATE vaults SET data = ? WHERE uid = ? AND name = ?""",
            (data, uid, name),
        )

    async def backup(self, backup_dir: Path) -> Path:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_name = f"{backup_dir}/backup_{timestamp}.db"
            backup_conn = sqlite3.connect(backup_name)
            self.connection.backup(backup_conn)
            backup_conn.commit()
            backup_conn.close()
            return backup_name
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"Failed to backup database: {e}")
