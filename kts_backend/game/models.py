from typing import Optional
from kts_backend.store.database.sqlalchemy_base import db
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    DateTime,
    Boolean,
    Integer,
    ForeignKey,
    ARRAY
)


class GameModel(db):
    __tablename__ = "games"
    id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime)
    chat_id = Column(BigInteger)
    last_name = Column(String)
    status = Column(Boolean)
    words = Column(ARRAY(String))
    gamescore = relationship('GameScoreModel', cascade='all,delete')

class GameScoreModel(db):
    __tablename__ = "gamescores"
    id = Column(BigInteger, primary_key=True)
    player_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'))
    game_id = Column(BigInteger, ForeignKey('games.id', ondelete='CASCADE'))
    points = Column(Integer)
    is_playing = Column(Boolean)
