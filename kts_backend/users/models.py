from typing import Optional

from kts_backend.store.database.sqlalchemy_base import db
from sqlalchemy import (
    Column,
    BigInteger,
    String
)
class UserModel(db):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    #email = Column(String, nullable=False)
    #password = Column(String, nullable=False)