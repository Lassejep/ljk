from secrets import choice
from string import ascii_letters, digits, punctuation

def generate_password(password_length: int) -> str:
    # Generate a random password of length password_length
    password = ''.join(choice(ascii_letters + digits + punctuation) for _ in range(password_length))
    return password