from sqlalchemy import Column, Integer, String
from clicx.database import models

class User(models.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)