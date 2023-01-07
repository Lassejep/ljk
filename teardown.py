from lib import database, encryption

db = database("data.db")
db.rm()
encryption.delete_key_pair()