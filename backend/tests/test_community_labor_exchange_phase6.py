import pytest

sqlalchemy = pytest.importorskip("sqlalchemy", reason="SQLAlchemy is required for community labor exchange tests")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import CommunityReputation, StarTransaction, User
from app.security import hash_password
from app.services.participation import (
    create_labor_verification_request,
    participation_summary,
    successful_verification_count,
    verify_labor_contribution,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _user(db_session, email):
    user = User(email=email, password_hash=hash_password("password123"), role="community_member")
    db_session.add(user)
    db_session.flush()
    return user


def test_three_member_verifications_award_original_member_and_verifiers(db_session):
    contributor = _user(db_session, "contributor@example.com")
    verifier_one = _user(db_session, "verifier-one@example.com")
    verifier_two = _user(db_session, "verifier-two@example.com")
    verifier_three = _user(db_session, "verifier-three@example.com")

    activity = create_labor_verification_request(
        db_session,
        user=contributor,
        labor_category="growth",
        activity_type_name="share_verified",
        source_module="social_share",
        proof_url="discord://share-proof",
        metadata={"platform": "TikTok", "content": "Library share"},
    )

    assert activity.verification_status == "pending"
    assert activity.star_award == 0
    assert activity.metadata_["labor_category"] == "growth"

    first = verify_labor_contribution(db_session, activity_id=activity.id, verifier=verifier_one, proof_url="discord://verify-1")
    second = verify_labor_contribution(db_session, activity_id=activity.id, verifier=verifier_two, proof_url="discord://verify-2")
    third = verify_labor_contribution(db_session, activity_id=activity.id, verifier=verifier_three, proof_url="discord://verify-3")

    assert first[2] is False
    assert first[3] == 3
    assert second[2] is False
    assert second[3] == 1
    assert third[2] is True
    assert third[3] == 1
    assert successful_verification_count(db_session, activity.id) == 3
    assert activity.verification_status == "verified"
    assert activity.star_award == 12

    contributor_summary = participation_summary(db_session, user_id=contributor.id)
    verifier_one_summary = participation_summary(db_session, user_id=verifier_one.id)
    verifier_two_summary = participation_summary(db_session, user_id=verifier_two.id)

    assert contributor_summary["star"] == 12
    assert verifier_one_summary["star"] == 3
    assert verifier_two_summary["star"] == 1
    assert db_session.query(StarTransaction).filter_by(activity_id=activity.id, user_id=contributor.id, amount=12).count() == 1

    contributor_rep = db_session.query(CommunityReputation).filter_by(user_id=contributor.id).one()
    verifier_rep = db_session.query(CommunityReputation).filter_by(user_id=verifier_one.id).one()
    assert contributor_rep.verified_contributions == 1
    assert contributor_rep.trust_score == 12
    assert verifier_rep.verifications_completed == 1
    assert verifier_rep.trust_score == 3


def test_member_cannot_verify_own_labor_request(db_session):
    contributor = _user(db_session, "self-check@example.com")
    activity = create_labor_verification_request(
        db_session,
        user=contributor,
        labor_category="builder",
        activity_type_name="documentation_improved",
        source_module="builder_labor",
    )

    with pytest.raises(ValueError, match="cannot verify their own"):
        verify_labor_contribution(db_session, activity_id=activity.id, verifier=contributor)
