import secrets
import base64

# Generate a 32-byte (256-bit) random key
key = secrets.token_bytes(32)
# Convert to base64 for storage
key_b64 = base64.b64encode(key).decode('utf-8')
print("Your encryption key:", key_b64) 