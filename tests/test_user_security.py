from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.security.passwords import (
    hash_password,
    verify_password,
)


def test_password_is_hashed():
    password = "Strong-Test-Password-123!"

    hashed = hash_password(password)

    assert hashed != password
    assert password not in hashed
    assert hashed.startswith("$argon2")


def test_correct_password_verifies():
    password = "Strong-Test-Password-123!"

    hashed = hash_password(password)

    assert verify_password(
        password,
        hashed,
    )


def test_wrong_password_is_rejected():
    hashed = hash_password(
        "Correct-Password-123!"
    )

    assert not verify_password(
        "Wrong-Password-123!",
        hashed,
    )


def test_empty_password_is_rejected():
    try:
        hash_password("")
    except ValueError:
        return

    raise AssertionError(
        "Empty password should be rejected."
    )


def test_user_can_be_persisted():
    engine = create_engine(
        "sqlite:///:memory:"
    )

    User.__table__.create(engine)

    Session = sessionmaker(bind=engine)

    with Session() as db:
        user = User(
            email="user@example.com",
            hashed_password=hash_password(
                "Strong-Password-123!"
            ),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.email == "user@example.com"
        assert user.is_active is True
        assert user.created_at is not None


def test_duplicate_email_is_rejected():
    engine = create_engine(
        "sqlite:///:memory:"
    )

    User.__table__.create(engine)

    Session = sessionmaker(bind=engine)

    with Session() as db:
        first = User(
            email="duplicate@example.com",
            hashed_password=hash_password(
                "Password-One-123!"
            ),
        )

        second = User(
            email="duplicate@example.com",
            hashed_password=hash_password(
                "Password-Two-123!"
            ),
        )

        db.add(first)
        db.commit()

        db.add(second)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return

        raise AssertionError(
            "Duplicate email should fail."
        )
