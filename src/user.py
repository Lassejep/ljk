class User:
    def __init__(self, user):
        self.id = user["id"]
        self.email = user["email"]
        self.salt = user["salt"]
        self.auth_key = user["auth_key"]
        self.vaults = []
        self.master_pass = None
