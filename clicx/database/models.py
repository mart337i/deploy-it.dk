
from clicx.database.sql import Curser
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Model(Base, Curser):
    __abstract__ = True
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
