from lib import database, encryption

db = database("test.db")
db.rm()
encryption.delete_key_pair()