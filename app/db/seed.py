from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User

SEED_PASSWORD = "Password123!"
# 50 so each Locust user can log in as its own account (see loadtest/locustfile.py).
SEED_EMAILS = [f"user{i}@example.com" for i in range(1, 51)]


def seed_users() -> None:
    db = SessionLocal()
    try:
        existing = set(db.scalars(select(User.email)).all())
        missing = [email for email in SEED_EMAILS if email not in existing]
        if not missing:
            print("Users already seeded, skipping.")
            return
        for email in missing:
            db.add(User(email=email, hashed_password=hash_password(SEED_PASSWORD)))
        db.commit()
        print(f"Seeded {len(missing)} users (password for all: {SEED_PASSWORD})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
