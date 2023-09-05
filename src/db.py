import sqlite3

class Vault:
    def __init__(self, user_id):
        self.user_id = user_id
        self.connection = sqlite3.connect(f"vault_{self.user_id}.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS vault(
                service_id INTEGER PRIMARY KEY,
                sefvice TEXT,
                username TEXT,
                password TEXT,
                notes TEXT
            )"""
        )

    def add_service(
        self, service, username, password, notes = ""
    ):
        self.cursor.execute(
            """INSERT INTO vault(
                service, username, password, notes
            ) VALUES(?, ?, ?, ?)""",
            (service, username, password, notes)
        )

    def find_service(self, service_id):
        self.cursor.execute(
            """SELECT * FROM vault WHERE service_id = ?""", (service_id,)
        )
        service = self.cursor.fetchone()
        return {
            "service_id": service[0],
            "service": service[1],
            "username": service[2],
            "password": service[3],
            "notes": service[4]
        }

    def delete_service(self, service_id):
        self.cursor.execute(
            """DELETE FROM vault WHERE service_id = ?""", (service_id,)
        )

    def update_service(
        self, service_id, service, username, password, notes = ""
    ):
        self.cursor.execute(
            """UPDATE vault SET
                service = ?,
                username = ?,
                password = ?,
                notes = ?
            WHERE service_id = ?""",
            (service, username, password, notes, service_id)
        )

    def get_services(self):
        self.cursor.execute(
            """SELECT * FROM vault"""
        )
        services = self.cursor.fetchall()
        services_list = []
        for service in services:
            services_list.append({
                "service_id": service[0],
                "service": service[1],
                "username": service[2],
                "password": service[3],
                "notes": service[4]
            })
        return services_list

    def search_services(self, service):
        self.cursor.execute(
            """SELECT * FROM vault WHERE service LIKE ?""", (service,)
        )
        services = self.cursor.fetchall()
        services_list = []
        for service in services:
            services_list.append({
                "service_id": service[0],
                "service": service[1],
                "username": service[2],
                "password": service[3],
                "notes": service[4]
            })
        return services_list
