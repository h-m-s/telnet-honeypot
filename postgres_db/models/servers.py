#!/usr/bin/python3                                                                                                                                                      
"""                                                                                                                                                                    
Definition for tweeted tweets mapping                                                                                                                                  
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from postgres_db.models.base import BaseModel, Base
from ipwhois import IPWhois

class Server(BaseModel, Base):
    """                                                                                                                                                                    Class for servers
    """
    __tablename__ = 'servers'
    server_id = Column(postgresql.UUID, primary_key=True)
    ip = Column(postgresql.INET)
    region = Column(String)
    date_created = Column(DateTime)
    last_checked = Column(DateTime)
