# -*- coding: utf-8 -*-

# -- stdlib --

# -- third party --
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# -- own --
from options import options


# -- code --
Model = declarative_base()
engine = create_engine(options.userdata_dburl)
session = scoped_session(sessionmaker(bind=engine))
