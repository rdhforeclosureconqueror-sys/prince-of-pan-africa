import pytest

sqlalchemy = pytest.importorskip("sqlalchemy", reason="SQLAlchemy is required for participation engine tests")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Activity, GuestSession, ParticipationPoint, StarTransaction, User
from app.security import hash_password
from app.services.participation import (
    available_opportunities,
    available_rewards,
    community_leaderboards,
    merge_guest_participation,
    participation_summary,
    submit_activity,
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


def test_guest_activity_records_generic_participation_tables(db_session):
    activity = submit_activity(
        db_session,
        user=None,
        guest_session_id="guest-phase1",
        activity_type_name="word_of_day_viewed",
        source_module="swahili",
        metadata={"word": "ujamaa"},
    )
    db_session.commit()

    assert activity.user_id is None
    assert activity.guest_session_id == "guest-phase1"
    assert activity.verification_status == "verified"
    assert activity.participation_points == 3
    assert activity.star_award == 3
    assert db_session.query(GuestSession).filter_by(session_id="guest-phase1").count() == 1
    assert db_session.query(ParticipationPoint).filter_by(activity_id=activity.id).count() == 1
    assert db_session.query(StarTransaction).filter_by(activity_id=activity.id).count() == 1


def test_guest_progress_merges_to_new_member(db_session):
    submit_activity(
        db_session,
        user=None,
        guest_session_id="guest-merge",
        activity_type_name="daily_history_read",
        source_module="history",
    )
    user = User(email="merge@example.com", password_hash=hash_password("password123"), role="community_member")
    db_session.add(user)
    db_session.flush()

    merged = merge_guest_participation(db_session, guest_session_id="guest-merge", user=user)
    db_session.commit()

    assert merged == 1
    activity = db_session.query(Activity).filter_by(guest_session_id="guest-merge").one()
    assert activity.user_id == user.id
    summary = participation_summary(db_session, user_id=user.id)
    assert summary["activity_count"] == 1
    assert summary["star"] == 3
    assert summary["current_rank"] == "Registered User"


def test_star_experience_helpers_use_engine_activity(db_session):
    user = User(email="star@example.com", password_hash=hash_password("password123"), role="community_member")
    db_session.add(user)
    db_session.flush()

    submit_activity(db_session, user=user, guest_session_id=None, activity_type_name="chapter_read", source_module="books")
    submit_activity(db_session, user=user, guest_session_id=None, activity_type_name="swahili_lesson_completed", source_module="swahili")
    db_session.commit()

    summary = participation_summary(db_session, user_id=user.id)
    assert summary["star"] == 17
    assert summary["activities_completed"] == 2
    assert summary["rank_progress"]["next_rank"] == "Community Member"
    assert summary["current_streak"] == 1
    assert any(item["activity_type"] == "chapter_read" for item in available_opportunities())
    assert available_rewards(summary["star"])[0]["star_needed"] == 8
    assert community_leaderboards(db_session)["top_readers"][0]["star"] == 10
