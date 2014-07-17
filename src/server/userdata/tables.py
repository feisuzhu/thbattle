# -*- coding: utf-8 -*-

# -- stdlib --

# -- third party --
from sqlalchemy import Column, Integer, Text, Float, Index

# -- own --
from .base import Model, engine


# -- code --
class Badges(Model):
    __tablename__ = 'badges'

    id    = Column(Integer, primary_key=True)
    uid   = Column(Integer, nullable=False)
    badge = Column(Text, nullable=False)


class PeerRating(Model):
    __tablename__ = 'peer_rating'

    id   = Column(Integer, primary_key=True)
    gid  = Column(Integer, nullable=False)    # game id
    uid1 = Column(Integer, nullable=False)    # user 1 (thinks)
    uid2 = Column(Integer, nullable=False)    # user 2
    vote = Column(Integer, nullable=False)    # played (well -> 1, sucks -> -1)

    __table_args__ = (
        Index('peer_rating_uniq', 'gid', 'uid1', 'uid2', unique=True),
    )


class PlayerRank(Model):
    # computed from PeerRating, using PageRank.
    __tablename__ = 'player_rank'
    uid   = Column(Integer, primary_key=True)
    score = Column(Float, nullable=False)


class GameResult(Model):
    __tablename__ = 'game_result'
    gid     = Column(Integer, primary_key=True)
    mode    = Column(Text, nullable=False)  # 'THBattleFaith'
    players = Column(Text, nullable=False)  # '2,123,43534,1231,345,144'
    winner  = Column(Text, nullable=False)  # '2,123,144'
    time    = Column(Text, nullable=False)  # datetime.isoformat()


# other things: game items, hidden character availability, etc.

Model.metadata.create_all(engine)
