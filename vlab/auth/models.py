"""User model — SQLAlchemy ORM + werkzeug password hashing."""

from __future__ import annotations

from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from vlab.database import Base, get_db

# Import column types lazily so the module is importable even before
# SQLAlchemy is installed (useful for tooling / linting).
try:
    from sqlalchemy import Column, DateTime, Integer, String
    from sqlalchemy.orm import Mapped, mapped_column
except ImportError:
    pass


class User(Base):
    __tablename__ = "users"

    if "Mapped" in globals():
        # Modern SA 2.0 declarative style
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        username: Mapped[str] = mapped_column(
            String(64), unique=True, nullable=False, index=True
        )
        email: Mapped[str] = mapped_column(
            String(255), unique=True, nullable=False, index=True
        )
        password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
    else:
        # Fallback for tooling that hasn't imported SA yet.
        pass

    def set_password(self, password: str) -> None:
        """Hash *password* and store it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return ``True`` if *password* matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    @classmethod
    def find_by_email(cls, email: str) -> User | None:
        """Look up a user by email address."""
        db = next(get_db())
        try:
            return db.query(cls).filter(cls.email == email).first()
        finally:
            db.close()

    @classmethod
    def find_by_username(cls, username: str) -> User | None:
        """Look up a user by username."""
        db = next(get_db())
        try:
            return db.query(cls).filter(cls.username == username).first()
        finally:
            db.close()

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"

    def to_dict(self) -> dict:
        """Serialize the user to a JSON-safe dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
