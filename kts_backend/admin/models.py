from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

from kts_backend.store.database.sqlalchemy_base import db
from sqlalchemy import (
    Column,
    String, Integer
)


@dataclass
class Admin:
    id: int
    email: str
    password: Optional[str] = None

    def is_password_valid(self, password: str):
        return self.password == sha256(password.encode()).hexdigest()

    @classmethod
    def from_session(cls, session: Optional[dict]) -> Optional["Admin"]:
        return cls(id=session["manager"]["id"], email=session["manager"]["email"])


class AdminModel(db):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
