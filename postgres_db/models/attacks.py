#!/usr/bin/python3                                                                                                                                                      
"""                                                                                                                                                                    
Definition for tweeted tweets mapping                                                                                                                                  
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from postgres_db.models.base import BaseModel, Base
from postgres_db.models.attackers import Attacker
from postgres_db.models.attack_patterns import Pattern
from postgres_db.models.servers import Server
import datetime

class Attack(BaseModel, Base):
    """                                                                                                                                                                    Class for attackers                                                                                                                                                    """
    __tablename__ = 'attacks'
    attack_id = Column(Integer, primary_key=True, autoincrement=True)
    attacker_ip = Column(postgresql.INET, ForeignKey("attackers.ip"))
    pattern_id = Column(Integer, ForeignKey("attack_patterns.pattern_id"))
    downloaded_files = Column(JSON)
    server_id = Column(postgresql.UUID, ForeignKey("servers.server_id"))
    timestamp = Column(DateTime)

    def __init__(self, attacker, pattern_id, host, timestamp):
        from postgres_db.models import storage
        self.attacker_ip = attacker.ip
        self.pattern_id = pattern_id
        self.host = host
        self.timestamp = timestamp
        self.server_id = storage.uuid

