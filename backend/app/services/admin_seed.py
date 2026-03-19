from app.database import get_db_connection
from app.security import hash_password

ADMIN_EMAIL = "rdhforeclosureconqueror@gmail.com"
ADMIN_PASSWORD = "beastmode"
ADMIN_ROLE = "admin"
ALLOWED_ROLES = {"admin", "operator", "viewer"}


def seed_admin() -> dict:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, email, role FROM users WHERE email = ?",
            (ADMIN_EMAIL,),
        ).fetchone()
        if row:
            return {"created": False, "email": row[1], "role": row[2]}

        conn.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (ADMIN_EMAIL, hash_password(ADMIN_PASSWORD), ADMIN_ROLE),
        )
        conn.commit()

    return {"created": True, "email": ADMIN_EMAIL, "role": ADMIN_ROLE}
