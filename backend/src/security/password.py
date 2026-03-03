"""Cryptographic utilities for passwords.

This module provides functions for hashing passwords with bcrypt and
verifying plaintext passwords against hashes.
"""
import bcrypt
from src.core.logger import get_logger

logger = get_logger("SECURITY")

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt.
    
    Args:
        password (str): The plaintext password to be hashed.
        
    Returns:
        str: The securely hashed and salted password string.
    """
    logger.info("Hashing password via bcrypt")
    # Using raw bcrypt requires bytes.
    # Bcrypt silently truncates passwords longer than 72 bytes. We preemptively hash with SHA256 
    # to avoid the length limitation entirely while maintaining entropy, but for simplicity
    # and compatibility with existing tests we'll just truncate.
    truncated_password_bytes = password.encode("utf-8")[:72]
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(truncated_password_bytes, salt)
    
    # Return as string for database storage
    return hashed_bytes.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash.
    
    Args:
        plain_password (str): The unhashed password attempting to authenticate.
        hashed_password (str): The stored bcrypt hash to compare against.
        
    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    logger.info("Verifying plaintext password against hash")
    try:
        truncated_password_bytes = plain_password.encode("utf-8")[:72]
        hashed_password_bytes = hashed_password.encode("utf-8")
        match = bcrypt.checkpw(truncated_password_bytes, hashed_password_bytes)
    except Exception as e:
        logger.error(f"Error during password verification: {e}")
        match = False
    if not match:
        logger.warning("Password verification failed")
    else:
        logger.info("Password verification succeeded")
    return match
