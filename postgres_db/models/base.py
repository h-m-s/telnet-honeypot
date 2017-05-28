#!/usr/bin/python3
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel():
    def save(self):
        """method to update self"""
        from postgres_db.models import storage
        storage.new(self)
        storage.save()
