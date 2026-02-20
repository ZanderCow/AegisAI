"""
Password Security Layer (security/password.py)
Handles password hashing and verification using bcrypt via passlib.
Requires: pip install passlib[bcrypt]
"""
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False  # silences the 72-byte truncation warning
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    Each call produces a unique hash due to random salting.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a stored bcrypt hash.
    Returns True if they match, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

# """
# Password Security Layer (security/password.py)
# Handles password hashing and verification using bcrypt via passlib.
# """

# from passlib.context import CryptContext
# import hashlib

# pwd_context = CryptContext(
#     schemes=["bcrypt"],
#     deprecated="auto"
# )


# def _prehash(password: str) -> str:
#     """
#     Convert password to fixed-length hex string using SHA256.
#     This avoids bcrypt's 72-byte limit entirely.
#     """
#     return hashlib.sha256(password.encode("utf-8")).hexdigest()


# def hash_password(password: str) -> str:
#     if not password:
#         raise ValueError("Password cannot be empty")

#     return pwd_context.hash(_prehash(password))


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     if not plain_password or not hashed_password:
#         return False

#     try:
#         return pwd_context.verify(
#             _prehash(plain_password),
#             hashed_password
#         )
#     except Exception:
#         return False