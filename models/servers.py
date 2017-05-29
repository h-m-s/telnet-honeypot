#!/usr/bin/python3                                                                                                                                                      
"""                                                                                                                                                                    
Definition for tweeted tweets mapping                                                                                                                                  
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from models.base import BaseModel, Base
from ipwhois import IPWhois
import datetime

class Server(BaseModel, Base):
    """                                                                                                                                                                    Class for servers
    """
    __tablename__ = 'servers'
    server_id = Column(postgresql.UUID, primary_key=True)
    ip = Column(postgresql.INET)
    region = Column(String)
    date_created = Column(DateTime)
    last_checked = Column(DateTime)
    name = Column(String)
    active = Column(Boolean)

    def __init__(self, server_id, ip, region, name):
        self.server_id = server_id
        self.ip = ip
        self.region = region
        self.name = name
        self.date_created = datetime.datetime.utcnow()
        self.last_checked = datetime.datetime.utcnow()
        self.active = True
        
