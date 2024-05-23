import unittest
from src import vault, encryption


class TestVault(unittest.TestCase):
    def setUp(self):
        self.vault_key = encryption.generate_vault_key()
        self.vault = vault.Vault("test", self.vault_key)
        self.vault.add(
            "test_service", "test_user", "test_password", "test_notes"
        )

    def test_search(self):
        service = self.vault.search("test_service")[0]
        self.assertEqual(service["service"], "test_service")
        self.assertEqual(service["user"], "test_user")
        self.assertEqual(service["password"], "test_password")
        self.assertEqual(service["notes"], "test_notes")

    def test_service(self):
        search = self.vault.search("test_service")[0]
        service = self.vault.service(search["id"])
        self.assertEqual(service["id"], search["id"])
        self.assertEqual(service["service"], "test_service")
        self.assertEqual(service["user"], "test_user")
        self.assertEqual(service["password"], "test_password")
        self.assertEqual(service["notes"], "test_notes")

    def test_update(self):
        search = self.vault.search("test_service")[0]
        self.vault.update(
            search["id"],
            "updated_service",
            "updated_user",
            "updated_password",
            "updated_notes",
        )
        service = self.vault.service(search["id"])
        self.assertEqual(service["service"], "updated_service")
        self.assertEqual(service["user"], "updated_user")
        self.assertEqual(service["password"], "updated_password")
        self.assertEqual(service["notes"], "updated_notes")

    def test_delete(self):
        search = self.vault.search("test_service")[0]
        self.vault.delete(search["id"])
        self.assertEqual(self.vault.service(search["id"]), None)

    def test_add(self):
        self.vault.add(
            "test_service_2", "test_user_2", "test_password_2", "test_notes_2"
        )
        old_service = self.vault.search("test_service")[0]
        service = self.vault.search("test_service_2")[0]
        self.assertNotEqual(old_service["id"], service["id"])
        self.assertEqual(service["service"], "test_service_2")
        self.assertEqual(service["user"], "test_user_2")
        self.assertEqual(service["password"], "test_password_2")
        self.assertEqual(service["notes"], "test_notes_2")

    def test_services(self):
        services = self.vault.services()
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["service"], "test_service")
        self.assertEqual(services[0]["user"], "test_user")
        self.assertEqual(services[0]["password"], "test_password")
        self.assertEqual(services[0]["notes"], "test_notes")
        self.vault.add(
            "test_service_2", "test_user_2", "test_password_2", "test_notes_2"
        )
        services = self.vault.services()
        self.assertEqual(len(services), 2)

    def test_search_multiple(self):
        self.vault.add(
            "test_service_2", "test_user_2", "test_password_2", "test_notes_2"
        )
        self.vault.add(
            "testing_service", "testing_user",
            "testing_password", "testing_notes"
        )
        self.vault.add(
            "testing_service", "testing_user"
            "testing_password", "test to see if this works"
        )
        services = self.vault.search("test_service")
        self.assertEqual(len(services), 2)
        self.assertEqual(services[0]["service"], "test_service")
        self.assertEqual(services[1]["service"], "test_service_2")

    def test_dump(self):
        data = self.vault.dump()
        self.assertNotEqual(data, None)

    def test_load(self):
        data = self.vault.dump()
        vault = vault.Vault("test", self.vault_key)
        self.assertNotEqual(vault.services(), self.vault.services())
        vault.load(data)
        self.assertEqual(vault.name, "test")
        self.assertEqual(vault.key, self.vault_key)
        self.assertEqual(vault.services(), self.vault.services())

    def tearDown(self):
        self.vault.rm()
