from secrets import choice
from string import ascii_letters, digits, punctuation
from src import encryption
from src.database import Database
from dotenv import find_dotenv, load_dotenv, set_key
from os import path, remove

def generate_password(password_length: int) -> str:
    password = ''.join(
        choice(ascii_letters + digits + punctuation)
        for _ in range(password_length)
    )
    return password

def generate_user(username: str, password: str) -> tuple[str, str, bytes]:
    hashed_password = encryption.hash_password(password)
    symmetrical_key = encryption.generate_symmetrical_key(password)
    return username, hashed_password, symmetrical_key

def generate_random_entry() -> tuple[str, str, str]:
    website = 'www.' + ''.join(
        choice(ascii_letters + digits) for _ in range(10)
    ) + '.com'
    username = ''.join(choice(ascii_letters + digits) for _ in range(10))
    password = generate_password(16)
    return website, username, password

def make_test_users(
    database: Database, number_of_users: int, number_of_entries: int
) -> None:    
    for i in range(number_of_users):
        username, hashed_password, symmetrical_key = generate_user(
            f"username{i}", "password"
        )
        encrypted_symmetrical_key = encryption.encrypt_symmetrical_key(
            symmetrical_key
        )
        database.add_user(username, hashed_password, encrypted_symmetrical_key)
        for _ in range(number_of_entries):
            website, username, password = generate_random_entry()
            encrypted_password = encryption.encrypt_password(
                password, symmetrical_key
            )
            database.add_service(
                website, username, encrypted_password, user_id=i+1
            )

def setup_client():
    if not path.exists(".env"):
        open(".env", "a").close()
        load_dotenv(find_dotenv())
        encryption.generate_key_pair()
        set_key(find_dotenv(), "PORT", "8765")
        set_key(find_dotenv(), "HOST", "localhost")

def teardown_client():
    remove(".env")

def setup_server():
    if not path.exists(".env"):
        open(".env", "a").close()
        load_dotenv(find_dotenv())
        set_key(find_dotenv(), "PORT", "8765")
        set_key(find_dotenv(), "HOST", "localhost")
    if not path.exists("data.db"):
        database = Database("data.db")
        database.add_users_table()
        database.add_services_table()

def teardown_server():
    remove(".env")
    remove("data.db")
