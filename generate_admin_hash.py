import bcrypt
import getpass

print("🔐 Admin password hash generator")

password = getpass.getpass("Enter admin password: ").encode()
hashed = bcrypt.hashpw(password, bcrypt.gensalt())

print("\n✅ Copy this hash into your backend .env file:\n")
print(hashed.decode())
