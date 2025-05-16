class UserDatabaseError(Exception):
    pass


class DuplicateEmailError(UserDatabaseError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"User with email: {email} already exists")


class UserNotFoundError(UserDatabaseError):
    def __init__(self, uid: int) -> None:
        self.uid = uid
        super().__init__(f"User with id: {uid} does not exist")
