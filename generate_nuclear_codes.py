import hashlib
import getpass

p = getpass.getpass(prompt='Password: ')
# Calculate the SHA-256 hash
hashed_string = hashlib.sha256(p.encode()).hexdigest()
print(hashed_string)
