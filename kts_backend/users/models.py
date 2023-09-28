from typing import Optional

from sqlalchemy.orm import relationship

from kts_backend.store.database.sqlalchemy_base import db
from sqlalchemy import (
    Column,
    BigInteger,
    String
)
class UserModel(db):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    vk_id = Column(BigInteger)
    name = Column(String)
    last_name = Column(String)

    gamescore = relationship('GameScoreModel', cascade='all,delete')
