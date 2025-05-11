import sqlite3
from typing import Any, Dict, List, Optional


class Vault:
    def __init__(self, name: str, key: str) -> None:
        self.name: str = name
        self.key: str = key
        self.connection: sqlite3.Connection = sqlite3.connect(":memory:")
        self.cursor: sqlite3.Cursor = self.connection.cursor()
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS vault(
                id INTEGER PRIMARY KEY,
                service TEXT,
                user TEXT,
                password TEXT,
                notes TEXT
            )"""
        )

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def rm(self) -> None:
        self.cursor.close()
        self.connection.close()

    def dump(self) -> bytes:
        self.connection.commit()
        return self.connection.serialize()

    def load(self, data: bytes) -> None:
        self.connection.deserialize(data)

    def add(
        self, service: str = "", user: str = "", password: str = "", notes: str = ""
    ) -> None:
        self.cursor.execute(
            """INSERT INTO vault(
                service, user, password, notes
            ) VALUES(?, ?, ?, ?)""",
            (service, user, password, notes),
        )

    def service(self, id: int) -> Optional[Dict[str, Any]]:
        self.cursor.execute("""SELECT * FROM vault WHERE id = ?""", (id,))
        service = self.cursor.fetchone()
        if not service:
            return None
        return {
            "id": service[0],
            "service": service[1],
            "user": service[2],
            "password": service[3],
            "notes": service[4],
        }

    def delete(self, id: int) -> None:
        self.cursor.execute("""DELETE FROM vault WHERE id = ?""", (id,))

    def update(
        self, id: int, service: str, user: str, password: str, notes: str = ""
    ) -> None:
        self.cursor.execute(
            """UPDATE vault SET
                service = ?,
                user = ?,
                password = ?,
                notes = ?
            WHERE id = ?""",
            (service, user, password, notes, id),
        )

    def services(self) -> Optional[List[Dict[str, Any]]]:
        self.cursor.execute("""SELECT * FROM vault""")
        services = self.cursor.fetchall()
        services_list = []
        if not services:
            return None
        for service in services:
            services_list.append(
                {
                    "id": service[0],
                    "service": service[1],
                    "user": service[2],
                    "password": service[3],
                    "notes": service[4],
                }
            )
        return services_list

    def search(self, service: str) -> Optional[List[Dict[str, Any]]]:
        service = f"%{service}%"
        self.cursor.execute(
            """SELECT * FROM vault WHERE service LIKE ? OR notes LIKE ?""",
            (service, service),
        )
        services = self.cursor.fetchall()
        if not services:
            return None
        services_list = []
        for service in services:
            services_list.append(
                {
                    "id": service[0],
                    "service": service[1],
                    "user": service[2],
                    "password": service[3],
                    "notes": service[4],
                }
            )
        return services_list
