from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import os
from django.conf import settings

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

def encrypt_file(file_data):
    """Encrypt file data using AES-256"""
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
    padding_length = 16 - (len(file_data) % 16)
    padded_data = file_data + bytes([padding_length] * padding_length)
    
    # Encrypt the data
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    
    # Combine salt, IV, and encrypted data
    return salt + iv + encrypted_data

def decrypt_file(encrypted_data):
    """Extract encryption parameters and return them with encrypted content"""
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    encrypted_content = encrypted_data[32:]
    
    return {
        'salt': base64.b64encode(salt).decode('utf-8'),
        'iv': base64.b64encode(iv).decode('utf-8'),
        'content': base64.b64encode(encrypted_content).decode('utf-8')
    } 