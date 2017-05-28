#!/usr/bin/python3                                                                                                                                                      
"""                                                                                                                                                                    
Definition for tweeted tweets mapping                                                                                                                                  
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from postgres_db.models.base import BaseModel, Base
from postgres_db.models.attackers import Attacker
from postgres_db.models.attack_patterns import Pattern
import datetime

class Attack(BaseModel, Base):
    """                                                                                                                                                                    Class for attackers                                                                                                                                                    """
    __tablename__ = 'attacks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    attacker_ip = Column(postgresql.INET, ForeignKey("attackers.ip"))
    pattern_id = Column(Integer, ForeignKey("attack_patterns.pattern_id"))
    host = Column(String)
    timestamp = Column(DateTime)

    def __init__(self, attacker, pattern_id, host, timestamp):
        self.attacker_ip = attacker.ip
        self.pattern_id = pattern_id
        self.host = host
        self.timestamp = timestamp

