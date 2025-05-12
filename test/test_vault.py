import unittest

from src.model import encryption, vault


class TestVault(unittest.TestCase):
    def setUp(self) -> None:
        self.vault_key = encryption.generate_vault_key()
        self.vault = vault.Vault("test", self.vault_key)
        self.vault.add("test_service", "test_user", "test_password", "test_notes")

    def test_search(self) -> None:
        search = self.vault.search("test_service")
        if search is None:
            self.fail("search is none")
        service = search[0]
        self.assertEqual(service["service"], "test_service")
        self.assertEqual(service["user"], "test_user")
        self.assertEqual(service["password"], "test_password")
        self.assertEqual(service["notes"], "test_notes")

    def test_service(self) -> None:
        search = self.vault.search("test_service")
        if search is None:
            self.fail("search is none")
        service = self.vault.service(search[0]["id"])
        if service is None:
            self.fail("sevice is none")
        self.assertEqual(service["service"], "test_service")
        self.assertEqual(service["user"], "test_user")
        self.assertEqual(service["password"], "test_password")
        self.assertEqual(service["notes"], "test_notes")

    def test_update(self) -> None:
        search = self.vault.search("test_service")
        if search is None:
            self.fail("search is none")
        service = search[0]
        self.vault.update(
            service["id"],
            "updated_service",
            "updated_user",
            "updated_password",
            "updated_notes",
        )
        updated_service = self.vault.service(service["id"])
        if updated_service is None:
            self.fail("updated service is none")
        self.assertEqual(updated_service["service"], "updated_service")
        self.assertEqual(updated_service["user"], "updated_user")
        self.assertEqual(updated_service["password"], "updated_password")
        self.assertEqual(updated_service["notes"], "updated_notes")

    def test_delete(self) -> None:
        search = self.vault.search("test_service")
        if search is None:
            self.fail("search is none")
        service = search[0]
        self.vault.delete(service["id"])
        self.assertEqual(self.vault.service(service["id"]), None)

    def test_add(self) -> None:
        self.vault.add(
            "test_service_2", "test_user_2", "test_password_2", "test_notes_2"
        )
        search = self.vault.search("test_service")
        if search is None:
            self.fail("search is none")
        service1 = search[0]
        service2 = search[1]

        self.assertNotEqual(service1["id"], service2["id"])
        self.assertEqual(service2["service"], "test_service_2")
        self.assertEqual(service2["user"], "test_user_2")
        self.assertEqual(service2["password"], "test_password_2")
        self.assertEqual(service2["notes"], "test_notes_2")

    def test_services(self) -> None:
        services = self.vault.services()
        if services is None:
            self.fail("services is none")
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["service"], "test_service")
        self.assertEqual(services[0]["user"], "test_user")
        self.assertEqual(services[0]["password"], "test_password")
        self.assertEqual(services[0]["notes"], "test_notes")
        self.vault.add(
            "test_service_2", "test_user_2", "test_password_2", "test_notes_2"
        )
        services = self.vault.services()
        if services is None:
            self.fail("services is none")
        self.assertEqual(len(services), 2)

    def test_search_multiple(self) -> None:
        self.vault.add(
            "test_service_2", "test_user_2", "test_password_2", "test_notes_2"
        )
        self.vault.add(
            "testing_service", "testing_user", "testing_password", "testing_notes"
        )
        self.vault.add(
            "testing_service",
            "testing_user" "testing_password",
            "test to see if this works",
        )
        services = self.vault.search("test_service")
        if services is None:
            self.fail("services is none")
        self.assertEqual(len(services), 2)
        self.assertEqual(services[0]["service"], "test_service")
        self.assertEqual(services[1]["service"], "test_service_2")

    def test_dump(self) -> None:
        data = self.vault.dump()
        self.assertNotEqual(data, None)

    def test_load(self) -> None:
        data = self.vault.dump()
        testvault = vault.Vault("test", self.vault_key)
        self.assertNotEqual(testvault.services(), self.vault.services())
        testvault.load(data)
        self.assertEqual(testvault.name, "test")
        self.assertEqual(testvault.key, self.vault_key)
        self.assertEqual(testvault.services(), self.vault.services())

    def tearDown(self) -> None:
        self.vault.rm()
