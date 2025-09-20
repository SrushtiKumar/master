"""
Common cryptographic utilities for the steganography toolkit.
Implements AES-256-GCM encryption, X25519 key exchange, Ed25519 signatures,
and HKDF-SHA256 for key derivation.
"""

import os
import gzip
from typing import Tuple, Optional, Dict, Any, Union, ByteString

from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
import reedsolo

# Constants
HEADER_SIZE = 16  # Size of the steganography header in bytes
RS_REDUNDANCY = 32  # Reed-Solomon redundancy bytes


class KeyManager:
    """Manages cryptographic keys for steganography operations."""
    
    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """Generate an X25519 key pair for key exchange."""
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        private_bytes = private_key.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=NoEncryption()
        )
        
        public_bytes = public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        
        return private_bytes, public_bytes
    
    @staticmethod
    def generate_signing_keypair() -> Tuple[bytes, bytes]:
        """Generate an Ed25519 key pair for digital signatures."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        private_bytes = private_key.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=NoEncryption()
        )
        
        public_bytes = public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        
        return private_bytes, public_bytes
    
    @staticmethod
    def generate_session_key() -> bytes:
        """Generate a random session key for AES encryption."""
        return os.urandom(32)  # 256 bits
    
    @staticmethod
    def wrap_session_key(session_key: bytes, recipient_public_key: bytes) -> bytes:
        """Encrypt a session key using recipient's public key."""
        # Convert recipient's public key bytes to a public key object
        public_key = x25519.X25519PublicKey.from_public_bytes(recipient_public_key)
        
        # Generate an ephemeral key pair for this exchange
        ephemeral_private = x25519.X25519PrivateKey.generate()
        ephemeral_public = ephemeral_private.public_key()
        
        # Perform the key exchange
        shared_key = ephemeral_private.exchange(public_key)
        
        # Derive an encryption key from the shared secret
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'session_key_wrap'
        ).derive(shared_key)
        
        # Encrypt the session key
        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, session_key, None)
        
        # Return ephemeral public key + nonce + ciphertext
        ephemeral_public_bytes = ephemeral_public.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        
        return ephemeral_public_bytes + nonce + ciphertext
    
    @staticmethod
    def unwrap_session_key(wrapped_key: bytes, private_key: bytes) -> bytes:
        """Decrypt a session key using recipient's private key."""
        # Extract components from the wrapped key
        ephemeral_public_bytes = wrapped_key[:32]
        nonce = wrapped_key[32:44]
        ciphertext = wrapped_key[44:]
        
        # Convert to key objects
        ephemeral_public = x25519.X25519PublicKey.from_public_bytes(ephemeral_public_bytes)
        private = x25519.X25519PrivateKey.from_private_bytes(private_key)
        
        # Perform the key exchange
        shared_key = private.exchange(ephemeral_public)
        
        # Derive the encryption key
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'session_key_wrap'
        ).derive(shared_key)
        
        # Decrypt the session key
        aesgcm = AESGCM(derived_key)
        session_key = aesgcm.decrypt(nonce, ciphertext, None)
        
        return session_key
    
    @staticmethod
    def sign_data(data: bytes, private_key: bytes) -> bytes:
        """Sign data using an Ed25519 private key."""
        signing_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
        signature = signing_key.sign(data)
        return signature
    
    @staticmethod
    def verify_signature(data: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify a signature using an Ed25519 public key."""
        try:
            verifying_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
            verifying_key.verify(signature, data)
            return True
        except Exception:
            return False
    
    @staticmethod
    def derive_seed(key: bytes, salt: bytes = None) -> bytes:
        """Derive a seed for CSPRNG from a key and optional salt."""
        if salt is None:
            salt = os.urandom(16)
            
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b'stego_seed'
        ).derive(key)
        
        return derived_key


class PayloadProcessor:
    """Processes payloads for steganography operations."""
    
    @staticmethod
    def prepare_payload(
        message: bytes, 
        session_key: bytes, 
        signing_key: bytes = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Prepare a payload for embedding:
        1. Compress with gzip
        2. Encrypt with AES-256-GCM
        3. Add error correction with Reed-Solomon
        4. Add a header with metadata
        
        Returns the prepared payload and metadata dictionary.
        """
        # Compress the message
        compressed = gzip.compress(message)
        
        # Generate a random nonce for AES-GCM
        nonce = os.urandom(12)
        
        # Encrypt the compressed message
        aesgcm = AESGCM(session_key)
        encrypted = aesgcm.encrypt(nonce, compressed, None)
        
        # Optionally sign the encrypted data
        signature = None
        if signing_key is not None:
            signature = KeyManager.sign_data(encrypted, signing_key)
            
        # Prepare the payload with metadata
        metadata = {
            "version": 1,
            "nonce": nonce,
            "has_signature": signature is not None
        }
        
        # Combine encrypted data and signature if present
        payload = encrypted
        if signature is not None:
            payload = signature + encrypted
            
        # Apply Reed-Solomon error correction
        rs = reedsolo.RSCodec(RS_REDUNDANCY)
        encoded_payload = rs.encode(payload)
        
        # Create a header with metadata
        header = os.urandom(HEADER_SIZE)  # Placeholder for a real header
        
        # Combine header and encoded payload
        final_payload = header + encoded_payload
        
        return final_payload, metadata
    
    @staticmethod
    def extract_payload(
        embedded_data: bytes, 
        session_key: bytes, 
        verify_key: bytes = None
    ) -> bytes:
        """
        Extract and process an embedded payload:
        1. Remove the header
        2. Apply Reed-Solomon error correction
        3. Verify signature if a verification key is provided
        4. Decrypt with AES-256-GCM
        5. Decompress with gzip
        
        Returns the original message.
        """
        # Extract header and payload
        header = embedded_data[:HEADER_SIZE]
        encoded_payload = embedded_data[HEADER_SIZE:]
        
        # Apply Reed-Solomon error correction
        rs = reedsolo.RSCodec(RS_REDUNDANCY)
        try:
            payload = rs.decode(encoded_payload)[0]
        except reedsolo.ReedSolomonError:
            raise ValueError("Too many errors in the embedded data to recover the payload")
        
        # Extract signature if present (simplified - in a real implementation, 
        # this would be determined from the header)
        signature = None
        encrypted = payload
        if verify_key is not None:
            # Assuming signature is 64 bytes for Ed25519
            signature = payload[:64]
            encrypted = payload[64:]
            
            # Verify the signature
            if not KeyManager.verify_signature(encrypted, signature, verify_key):
                raise ValueError("Signature verification failed")
        
        # Extract nonce (simplified - in a real implementation, this would be in the header)
        nonce = header[:12]  # Using part of the header as nonce for demonstration
        
        # Decrypt the payload
        aesgcm = AESGCM(session_key)
        try:
            compressed = aesgcm.decrypt(nonce, encrypted, None)
        except Exception:
            raise ValueError("Decryption failed - incorrect key or corrupted data")
        
        # Decompress the message
        try:
            message = gzip.decompress(compressed)
        except Exception:
            raise ValueError("Decompression failed - data may be corrupted")
        
        return message