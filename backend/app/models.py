from dataclasses import dataclass


@dataclass
class User:
    id: int
    email: str
    password_hash: str
    role: str
    created_at: str


@dataclass
class LeadershipAssessment:
    id: int
    user_id: str
    responses: str
    scores: str
    version: str
    created_at: str
