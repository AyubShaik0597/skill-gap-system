
from getpass import getpass

from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.models import User
from app.security.utils import hash_password


def main():
    # Create any missing tables without dropping existing data.
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # This bootstrap is permitted only before any account exists.
        if db.query(User).count() > 0:
            print(
                "STOP: An account already exists. "
                "Bootstrap is disabled."
            )
            return

        email = input("Administrator email: ").strip().lower()
        full_name = input("Administrator full name: ").strip()

        if not email or "@" not in email:
            print("Invalid email.")
            return

        if len(full_name) < 2 or len(full_name) > 150:
            print("Full name must contain 2–150 characters.")
            return

        password = getpass("Administrator password (12+ characters): ")
        confirmation = getpass("Confirm password: ")

        if password != confirmation:
            print("Passwords do not match.")
            return

        try:
            hashed_password = hash_password(password)
        except ValueError as exc:
            print(exc)
            return

        admin = User(
            email=email,
            full_name=full_name,
            password_hash=hashed_password,
            role="Admin",
            employee_id=None,
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("SUCCESS: Initial administrator account created.")
        print("You can now log in through /api/auth/login.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
