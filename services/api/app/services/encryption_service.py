"""
Encryption service for sensitive data at rest.

Security requirements:
- In production: ENCRYPTION_KEY is required, missing key fails startup
- In development: temporary key with clear warning, data unreadable after restart
- Uses Fernet symmetric encryption with base64-encoded keys
- All encrypted values prefixed with "enc:v1:" for detection
"""

import os
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class EncryptionService:
    """Handles field-level encryption for sensitive data."""
    
    ENCRYPTED_PREFIX = "enc:v1:"
    
    def __init__(self):
        key = os.environ.get("ENCRYPTION_KEY")
        
        if not key:
            env = os.environ.get("ENV", "development")
            if env == "production":
                raise RuntimeError(
                    "ENCRYPTION_KEY environment variable is required in production. "
                    "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )
            else:
                logger.warning(
                    "⚠️  WARNING: ENCRYPTION_KEY not set. Using temporary key for development. "
                    "⚠️  WARNING: Encrypted data will become UNREADABLE after server restart. "
                    "⚠️  WARNING: Set a stable ENCRYPTION_KEY in .env for development."
                )
                key = Fernet.generate_key().decode()
        
        self.cipher = Fernet(key.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext and add version prefix.
        Always encrypts, never leaves data unencrypted.
        """
        if not plaintext:
            return plaintext
        
        encrypted = self.cipher.encrypt(plaintext.encode()).decode()
        return self.ENCRYPTED_PREFIX + encrypted
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext if prefixed, otherwise return as-is.
        Supports backward compatibility with legacy plaintext data.
        """
        if not ciphertext:
            return ciphertext
        
        if ciphertext.startswith(self.ENCRYPTED_PREFIX):
            actual = ciphertext[len(self.ENCRYPTED_PREFIX):]
            return self.cipher.decrypt(actual.encode()).decode()
        else:
            # Legacy plaintext — return as-is
            return ciphertext


# Singleton instance
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """Get or create the singleton encryption service."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service