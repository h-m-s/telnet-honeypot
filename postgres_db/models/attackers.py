#!/usr/bin/python3                                                                                                                                                      
"""                                                                                                                                                                    
Definition for tweeted tweets mapping                                                                                                                                  
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from postgres_db.models.base import BaseModel, Base

class Attacker(BaseModel, Base):
    """                                                                                                                                                                    Class for attackers                                                                                                                                                    """
    __tablename__ = 'attackers'
    ip = Column(postgresql.INET, primary_key=True)
    count = Column(Integer, nullable=False)

    def __init__(self, ip):
        self.ip = ip
        self.count = 1

