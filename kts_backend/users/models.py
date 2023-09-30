from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import relationship

from kts_backend.store.database.sqlalchemy_base import db
from sqlalchemy import (
    Column,
    BigInteger,
    String
)


@dataclass
class UserDC:
    id: int
    vk_id: int
    name: str
    last_name: str


class UserModel(db):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    vk_id = Column(BigInteger)
    name = Column(String)
    last_name = Column(String)

    gamescore = relationship('GameScoreModel', cascade='all,delete')
