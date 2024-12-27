from cryptography.fernet import Fernet
from django.conf import settings
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

def get_encryption_key():
    # In production, use a proper key management system
    salt = b'salt_'  # Use a secure random salt in production
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.FILE_ENCRYPTION_KEY.encode()))
    return Fernet(key)

def encrypt_file(file_data):
    fernet = get_encryption_key()
    return fernet.encrypt(file_data)

def decrypt_file(encrypted_data):
    fernet = get_encryption_key()
    return fernet.decrypt(encrypted_data) 