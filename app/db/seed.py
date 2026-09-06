from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User

SEED_PASSWORD = "Password123!"
SEED_EMAILS = [f"user{i}@example.com" for i in range(1, 6)]


def seed_users() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(User)) is not None:
            print("Users already seeded, skipping.")
            return
        for email in SEED_EMAILS:
            db.add(User(email=email, hashed_password=hash_password(SEED_PASSWORD)))
        db.commit()
        print(f"Seeded {len(SEED_EMAILS)} users (password for all: {SEED_PASSWORD})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
