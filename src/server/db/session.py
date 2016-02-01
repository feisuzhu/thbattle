# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# -- own --
from options import options
from server.db.base import Model


# -- code --
import server.db.models  # noqa

engine = create_engine(options.db, encoding='utf-8', convert_unicode=True)
Model.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
