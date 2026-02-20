"""
Password Security Layer (security/password.py)
Handles password hashing and verification using bcrypt directly.
Requires: pip install bcrypt
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    Each call produces a unique hash due to random salting.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a stored bcrypt hash.
    Returns True if they match, False otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False
