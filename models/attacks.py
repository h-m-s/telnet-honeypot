#!/usr/bin/python3
"""
Module to map attack objects to Postgres DB
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from models.base import BaseModel, Base
from models.attackers import Attacker
from models.attack_patterns import Pattern
from models.servers import Server
import datetime

class Attack(BaseModel, Base):
    """
    Class definition to map attack objects to Postgres DB
    """
    __tablename__ = 'attacks'
    attack_id = Column(Integer, primary_key=True, autoincrement=True)
    attacker_ip = Column(postgresql.INET, ForeignKey("attackers.ip"))
    pattern_id = Column(Integer, ForeignKey("attack_patterns.pattern_id"))
    downloaded_files = Column(JSON)
    server_id = Column(postgresql.UUID, ForeignKey("servers.server_id"))
    timestamp = Column(DateTime)

    def __init__(self, attacker, pattern_id, host, timestamp, files):
        from models import storage
        self.attacker_ip = attacker.ip
        self.pattern_id = pattern_id
        self.host = host
        self.timestamp = timestamp
        self.server_id = storage.session.query(Server).filter(Server.ip == storage.ip).one().server_id
        self.downloaded_files = files
