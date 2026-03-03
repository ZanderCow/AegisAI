"""Unit tests for the password security module.

This module contains unit tests verifying the behavior of bcrypt password hashing
and verification functions inside the `src.security.password` module.
"""
import pytest
from src.security.password import hash_password, verify_password

def test_hash_password() -> None:
    """Tests that a password hashes successfully and uniquely.
    
    Verifies that the `hash_password` function returns a valid bcrypt hash
    that is different from the plaintext password, and that two identical
    passwords produce different hashes due to salting.
    """
    password = "supersecurepassword123"
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)
    
    assert hashed1 != password
    assert hashed1.startswith("$2b$")
    # Due to salting, two hashes of the same password must not be identical
    assert hashed1 != hashed2

def test_verify_password_success() -> None:
    """Tests successful verification of a correct password.
    
    Verifies that a valid plaintext password successfully matches 
    its corresponding bcrypt hash.
    """
    password = "supersecurepassword123"
    hashed = hash_password(password)
    
    result = verify_password(password, hashed)
    assert result is True

def test_verify_password_failure_wrong_password() -> None:
    """Tests that an incorrect password fails verification.
    
    Verifies that providing an incorrect plaintext password for a valid
    hash returns False.
    """
    password = "supersecurepassword123"
    wrong_password = "wrongpassword123"
    hashed = hash_password(password)
    
    result = verify_password(wrong_password, hashed)
    assert result is False

def test_verify_password_failure_invalid_hash() -> None:
    """Tests that an invalid hash format safely returns False.
    
    Verifies that passing a malformed or invalid hash string to the
    verification function gets cleanly caught and returns False instead
    of throwing an exception.
    """
    password = "supersecurepassword123"
    invalid_hash = "not_a_real_bcrypt_hash"
    
    result = verify_password(password, invalid_hash)
    assert result is False

def test_password_truncation() -> None:
    """Tests bcrypt password truncation fallback behavior.
    
    Verifies that extremely long passwords exceeding bcrypt's 72-byte
    limit are safely truncated securely as implemented in the module.
    """
    long_password = "a" * 100
    hashed = hash_password(long_password)
    
    # It should succeed without raising a value error from bcrypt
    result1 = verify_password(long_password, hashed)
    assert result1 is True
    
    # Since it is truncated to 72 chars, providing 72 chars should match
    # because the excess chars were thrown out during hashing!
    result2 = verify_password("a" * 72, hashed)
    assert result2 is True
