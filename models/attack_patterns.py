#!/usr/bin/python3                                                                                                                                                      
"""                                                                                                                                                                    
Definition for tweeted tweets mapping                                                                                                                                  
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from models.base import BaseModel, Base

class Pattern(BaseModel, Base):
    """                                                                                                                                                                    Class for attackers                                                                                                                                                    """
    __tablename__ = 'attack_patterns'
    pattern_id = Column(Integer, primary_key=True, autoincrement=True)
    pattern = Column(String(500))
    pattern_md5 = Column(Text)
    count = Column(Integer, nullable=False)

    def __init__(self, sanitized_pattern, pattern_md5):
        self.pattern = sanitized_pattern
        self.pattern_md5 = pattern_md5
        self.count = 1
        print(self.pattern)

