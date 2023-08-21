from secrets import choice
from string import ascii_letters, digits, punctuation
from src import encryption
from src.database import Database

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

def setup():
    open(".env", "a").close()
    encryption.generate_key_pair()
    db = Database("data.db")
    db.add_users_table()
    db.add_services_table()

def teardown():
    db = Database("data.db")
    db.rm()
    encryption.delete_key_pair()
