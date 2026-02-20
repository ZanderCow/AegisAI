"""
Unit Tests — Password Security Layer (security/password.py)
Tests: hash_password, verify_password
Run with: pytest tests/unit/test_password.py -v
"""
import pytest
from src.security.password import hash_password, verify_password


class TestHashPassword:
    def test_returns_a_string(self):
        result = hash_password("mysecret")
        assert isinstance(result, str)

    def test_hash_is_not_plaintext(self):
        password = "mysecret"
        assert hash_password(password) != password

    def test_same_password_produces_different_hashes(self):
        """bcrypt uses a random salt — two hashes of the same input should differ."""
        hash1 = hash_password("samepass")
        hash2 = hash_password("samepass")
        assert hash1 != hash2

    def test_hash_is_non_empty(self):
        assert len(hash_password("anypass")) > 0


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        password = "correctpass"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correctpass")
        assert verify_password("wrongpass", hashed) is False

    def test_empty_password_returns_false(self):
        hashed = hash_password("somepass")
        assert verify_password("", hashed) is False

    def test_similar_password_returns_false(self):
        """Case-sensitive — Password123 and password123 must not match."""
        hashed = hash_password("Password123")
        assert verify_password("password123", hashed) is False

    def test_plaintext_against_plaintext_returns_false(self):
        """Passing a non-hashed string as the hash should not verify."""
        assert verify_password("password", "password") is False