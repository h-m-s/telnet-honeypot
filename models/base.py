#!/usr/bin/python3
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel():
    def save(self):
        """method to update self"""
        from models import storage
        storage.new(self)
        storage.save()
