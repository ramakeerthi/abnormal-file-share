from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def generate_key(password, salt):
    """Generate an AES key from password and salt using PBKDF2"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode())
    return key

def encrypt_file(data):
    print("\n=== Server Encryption Started ===")
    print(f"Input data size: {len(data)}")
    print(f"First 50 bytes of input: {data[:50]}")
    
    # Generate a random salt
    salt = os.urandom(16)
    # Generate encryption key
    key = generate_key(settings.FILE_ENCRYPTION_KEY, salt)
    # Generate random IV
    iv = os.urandom(16)
    
    # Create AES cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    
    # Pad the data
    padding_length = 16 - (len(data) % 16)
    padded_data = data + bytes([padding_length] * padding_length)
    
    # Encrypt the data
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    
    print(f"Encrypted data size: {len(encrypted_data)}")
    print(f"First 50 bytes of encrypted: {encrypted_data[:50]}")
    print("=== Server Encryption Complete ===\n")
    return salt + iv + encrypted_data

def decrypt_file(encrypted_data):
    print("\n=== Server Decryption Started ===")
    print(f"Input data size: {len(encrypted_data)}")
    print(f"First 50 bytes of input: {encrypted_data[:50]}")
    
    # Extract salt, iv and encrypted content
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    encrypted_content = encrypted_data[32:]
    
    # Generate decryption key
    key = generate_key(settings.FILE_ENCRYPTION_KEY, salt)
    
    # Create AES cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    
    # Decrypt the data
    decrypted_data = decryptor.update(encrypted_content) + decryptor.finalize()
    
    # Remove padding
    padding_length = decrypted_data[-1]
    decrypted_data = decrypted_data[:-padding_length]
    
    print(f"Decrypted data size: {len(decrypted_data)}")
    print(f"First 50 bytes of decrypted: {decrypted_data[:50]}")
    print("=== Server Decryption Complete ===\n")
    
    return decrypted_data 