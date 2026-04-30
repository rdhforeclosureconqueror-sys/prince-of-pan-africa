import base64
import hashlib
import hmac
import secrets

PBKDF2_SCHEME = "pbkdf2_sha256"
# We use stdlib PBKDF2-SHA256 because this environment cannot reliably install
# external password-hashing packages (bcrypt/argon2), and PBKDF2 remains
# supported across current and upcoming Python runtimes (including 3.13+).
PBKDF2_ITERATIONS = 390000
SALT_BYTES = 16


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64_decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"{PBKDF2_SCHEME}${PBKDF2_ITERATIONS}${_b64_encode(salt)}${_b64_encode(digest)}"


def _is_legacy_sha256_hash(stored_hash: str) -> bool:
    return len(stored_hash) == 64 and all(char in "0123456789abcdef" for char in stored_hash.lower())


def _is_pbkdf2_hash(stored_hash: str) -> bool:
    return stored_hash.startswith(f"{PBKDF2_SCHEME}$")


def _verify_pbkdf2_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, rounds_raw, salt_raw, digest_raw = stored_hash.split("$", 3)
        if scheme != PBKDF2_SCHEME:
            return False
        rounds = int(rounds_raw)
        salt = _b64_decode(salt_raw)
        expected_digest = _b64_decode(digest_raw)
    except (TypeError, ValueError):
        return False

    actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return hmac.compare_digest(actual_digest, expected_digest)


def verify_password(password: str, stored_hash: str) -> tuple[bool, bool]:
    """Return (is_valid, should_upgrade_hash)."""
    if not stored_hash:
        return False, False

    if _is_pbkdf2_hash(stored_hash):
        return _verify_pbkdf2_password(password, stored_hash), False

    if _is_legacy_sha256_hash(stored_hash):
        legacy_valid = hashlib.sha256(password.encode("utf-8")).hexdigest() == stored_hash
        return legacy_valid, legacy_valid

    return False, False
