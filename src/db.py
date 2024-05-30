import sqlite3


class Database:
    def __init__(self, database_name):
        self.database_name = database_name
        self.connection = sqlite3.connect(self.database_name)
        self.cursor = self.connection.cursor()
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

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()

    def add_user(self, email, auth_key):
        try:
            self.cursor.execute(
                """INSERT INTO users(
                    email, auth_key
                ) VALUES (?, ?)""",
                (email, auth_key)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"User with email: {email} already exists")

    def delete_user(self, uid):
        try:
            self.cursor.execute(
                """DELETE FROM users WHERE id = ?""", (uid,)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"User with id: {uid} does not exist")

    def get_user(self, uid):
        self.cursor.execute(
            """SELECT * FROM users WHERE id = ?""", (uid,)
        )
        user = self.cursor.fetchone()
        if user is not None:
            return {
                "id": user[0],
                "email": user[1],
                "auth_key": user[2],
            }
        else:
            raise Exception(f"User with id: {uid} not found")

    def update_email(self, uid, new_email, new_auth_key):
        try:
            self.cursor.execute(
                """UPDATE users SET email = ?, auth_key = ? WHERE id = ?""",
                (new_email, new_auth_key, uid)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"User with email: {new_email} already exists")

    def update_auth_key(self, uid, auth_key):
        try:
            self.cursor.execute(
                """UPDATE users SET auth_key = ? WHERE id = ?""",
                (auth_key, uid)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"User with id: {uid} does not exist")

    def get_id(self, email):
        self.cursor.execute(
            """SELECT id FROM users WHERE email = ?""", (email,)
        )
        id = self.cursor.fetchone()
        if id is not None:
            return id[0]
        else:
            raise Exception(f"User with email: {email} not found")

    def get_auth_key(self, uid):
        self.cursor.execute(
            """SELECT auth_key FROM users WHERE id = ?""", (uid,)
        )
        auth_key = self.cursor.fetchone()
        if auth_key is not None:
            return auth_key[0]
        else:
            raise Exception(f"User with id: {uid} not found")

    def add_vault(self, uid, name, key, data):
        if name.strip() == "":
            raise Exception("Vault name cannot be empty")
        try:
            self.cursor.execute(
                """INSERT INTO vaults(
                    uid, name, key, data
                ) VALUES (?, ?, ?, ?)""",
                (uid, name, key, data)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"Vault with name: {name} already exists")

    def delete_vault(self, uid, name):
        try:
            self.cursor.execute(
                """DELETE FROM vaults WHERE uid = ? AND name = ?""",
                (uid, name)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"Vault with name: {name} does not exist")

    def get_vaults(self, uid):
        self.cursor.execute(
            """SELECT * FROM vaults WHERE uid = ?""", (uid,)
        )
        vaults = self.cursor.fetchall()
        if len(vaults) > 0:
            return [
                {
                    "id": vault[0],
                    "uid": vault[1],
                    "name": vault[2],
                    "key": vault[3],
                    "data": vault[4],
                } for vault in vaults
            ]
        else:
            raise Exception(f"User with id: {uid} has no vaults")

    def get_vault(self, uid, name):
        self.cursor.execute(
            """SELECT * FROM vaults WHERE uid = ? AND name = ?""",
            (uid, name)
        )
        vault = self.cursor.fetchone()
        if vault is not None:
            return {
                "id": vault[0],
                "uid": vault[1],
                "name": vault[2],
                "key": vault[3],
                "data": vault[4],
            }
        else:
            raise Exception(f"Vault with name: {name} not found")

    def get_vault_key(self, uid, name):
        vault = self.get_vault(uid, name)
        return vault["key"]

    def get_vault_data(self, uid, name):
        vault = self.get_vault(uid, name)
        return vault["data"]

    def get_vault_id(self, uid, name):
        vault = self.get_vault(uid, name)
        return vault["id"]

    def update_vault_name(self, uid, name, new_name):
        try:
            self.cursor.execute(
                """UPDATE vaults SET name = ? WHERE uid = ? AND name = ?""",
                (new_name, uid, name)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"Vault with name: {new_name} already exists")

    def update_vault_key(self, uid, name, key):
        try:
            self.cursor.execute(
                """UPDATE vaults SET key = ? WHERE uid = ? AND name = ?""",
                (key, uid, name)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"Vault with name: {name} does not exist")

    def update_vault(self, uid, name, data):
        try:
            self.cursor.execute(
                """UPDATE vaults SET data = ? WHERE uid = ? AND name = ?""",
                (data, uid, name)
            )
        except sqlite3.IntegrityError:
            raise Exception(f"Vault with name: {name} does not exist")
