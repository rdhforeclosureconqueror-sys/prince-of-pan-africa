from dataclasses import dataclass


@dataclass
class User:
    id: int
    email: str
    password_hash: str
    role: str
    created_at: str
