import hashlib

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _is_legacy_sha256_hash(stored_hash: str) -> bool:
    return len(stored_hash) == 64 and all(char in "0123456789abcdef" for char in stored_hash.lower())


def verify_password(password: str, stored_hash: str) -> tuple[bool, bool]:
    """Return (is_valid, should_upgrade_hash)."""
    if not stored_hash:
        return False, False

    if stored_hash.startswith("$2"):
        try:
            return pwd_context.verify(password, stored_hash), False
        except ValueError:
            return False, False

    if _is_legacy_sha256_hash(stored_hash):
        legacy_valid = hashlib.sha256(password.encode("utf-8")).hexdigest() == stored_hash
        return legacy_valid, legacy_valid

    return False, False
