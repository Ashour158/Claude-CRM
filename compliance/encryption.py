# compliance/encryption.py
# Field-level encryption utilities with KMS support

import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from django.conf import settings
import hashlib
import hmac


class SecretEncryption:
    """Encryption utilities for secrets with envelope encryption"""
    
    def __init__(self):
        # Use settings or environment variable for master key
        self.master_key = getattr(
            settings, 
            'ENCRYPTION_MASTER_KEY', 
            os.environ.get('ENCRYPTION_MASTER_KEY', 'default-master-key-change-in-production')
        )
    
    def encrypt(self, plaintext: str, kms_key_id: str = None) -> str:
        """
        Encrypt data using envelope encryption
        
        Args:
            plaintext: Data to encrypt
            kms_key_id: Optional KMS key ID for encryption
            
        Returns:
            Encrypted data as base64 string
        """
        # Generate data encryption key (DEK)
        dek = Fernet.generate_key()
        
        # Encrypt plaintext with DEK
        cipher = Fernet(dek)
        encrypted_data = cipher.encrypt(plaintext.encode())
        
        # Encrypt DEK with master key (simulating KMS)
        encrypted_dek = self._encrypt_dek(dek, kms_key_id)
        
        # Combine encrypted DEK and data
        envelope = {
            'encrypted_dek': base64.b64encode(encrypted_dek).decode(),
            'encrypted_data': base64.b64encode(encrypted_data).decode(),
            'kms_key_id': kms_key_id or 'default'
        }
        
        return json.dumps(envelope)
    
    def decrypt(self, encrypted_envelope: str, kms_key_id: str = None) -> str:
        """
        Decrypt data using envelope encryption
        
        Args:
            encrypted_envelope: Encrypted envelope as JSON string
            kms_key_id: Optional KMS key ID for decryption
            
        Returns:
            Decrypted plaintext
        """
        try:
            envelope = json.loads(encrypted_envelope)
            
            # Decrypt DEK with master key
            encrypted_dek = base64.b64decode(envelope['encrypted_dek'])
            dek = self._decrypt_dek(encrypted_dek, envelope.get('kms_key_id'))
            
            # Decrypt data with DEK
            encrypted_data = base64.b64decode(envelope['encrypted_data'])
            cipher = Fernet(dek)
            plaintext = cipher.decrypt(encrypted_data)
            
            return plaintext.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def _encrypt_dek(self, dek: bytes, kms_key_id: str = None) -> bytes:
        """Encrypt data encryption key with master key"""
        # Use PBKDF2 to derive encryption key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'crm-encryption-salt',  # In production, use unique salt
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        
        cipher = Fernet(key)
        return cipher.encrypt(dek)
    
    def _decrypt_dek(self, encrypted_dek: bytes, kms_key_id: str = None) -> bytes:
        """Decrypt data encryption key with master key"""
        # Use PBKDF2 to derive encryption key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'crm-encryption-salt',  # Must match encryption salt
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        
        cipher = Fernet(key)
        return cipher.decrypt(encrypted_dek)


class PIIEncryption:
    """Field-level encryption for PII data"""
    
    @staticmethod
    def encrypt_field(value: str, field_name: str = None) -> str:
        """
        Encrypt PII field value
        
        Args:
            value: Field value to encrypt
            field_name: Optional field name for key derivation
            
        Returns:
            Encrypted value
        """
        if not value:
            return value
        
        encryption = SecretEncryption()
        return encryption.encrypt(value)
    
    @staticmethod
    def decrypt_field(encrypted_value: str, field_name: str = None) -> str:
        """
        Decrypt PII field value
        
        Args:
            encrypted_value: Encrypted field value
            field_name: Optional field name for key derivation
            
        Returns:
            Decrypted value
        """
        if not encrypted_value:
            return encrypted_value
        
        encryption = SecretEncryption()
        return encryption.decrypt(encrypted_value)
    
    @staticmethod
    def is_encrypted(value: str) -> bool:
        """Check if value is encrypted"""
        if not value:
            return False
        
        try:
            data = json.loads(value)
            return 'encrypted_dek' in data and 'encrypted_data' in data
        except:
            return False


class EncryptedField:
    """Database field wrapper for automatic encryption/decryption"""
    
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    def encrypt(self, value: str) -> str:
        """Encrypt value before storage"""
        return PIIEncryption.encrypt_field(value, self.field_name)
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt value after retrieval"""
        return PIIEncryption.decrypt_field(encrypted_value, self.field_name)


class DataMasking:
    """Utilities for data masking"""
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email address"""
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = local[0] + '*'
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number"""
        if not phone:
            return phone
        
        # Remove non-digit characters
        digits = ''.join(c for c in phone if c.isdigit())
        
        if len(digits) < 4:
            return '*' * len(digits)
        
        return '*' * (len(digits) - 4) + digits[-4:]
    
    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Mask SSN"""
        if not ssn:
            return ssn
        
        # Remove non-digit characters
        digits = ''.join(c for c in ssn if c.isdigit())
        
        if len(digits) != 9:
            return '*' * len(digits)
        
        return '***-**-' + digits[-4:]
    
    @staticmethod
    def mask_credit_card(card: str) -> str:
        """Mask credit card number"""
        if not card:
            return card
        
        # Remove non-digit characters
        digits = ''.join(c for c in card if c.isdigit())
        
        if len(digits) < 4:
            return '*' * len(digits)
        
        return '*' * (len(digits) - 4) + digits[-4:]
