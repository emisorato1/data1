"""Password hashing y verification con bcrypt.

OWASP: cost factor 12 para balance seguridad/performance.
"""

import bcrypt

_BCRYPT_ROUNDS = 12


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password with bcrypt (cost factor 12).

    Bcrypt truncates input at 72 bytes; we truncate explicitly to
    avoid ``ValueError`` from newer bcrypt versions.
    """
    password_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")  # type: ignore[no-any-return]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Returns ``True`` if the password matches, ``False`` otherwise.
    Handles invalid hashes gracefully by returning ``False``.
    """
    try:
        return bcrypt.checkpw(  # type: ignore[no-any-return]
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False
