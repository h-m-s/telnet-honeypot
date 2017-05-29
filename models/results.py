#!/usr/bin/python3
import datetime
import json
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from models.base import BaseModel, Base
from parse import attacks_since, total_attacks, total_attack_patterns, top_clients, asn_count
from ping import check_servers

class Results(BaseModel, Base):
    __tablename__ = 'parsing_results'
    time_results_parsed = Column(DateTime, primary_key=True)
    last_hr = Column(Integer)
    last_24_hrs = Column(Integer)
    last_week = Column(Integer)
    last_month = Column(Integer)
    total_malware_md5s = Column(Integer)
    total = Column(Integer)
    total_attack_patterns = Column(Integer)
    top_asns = Column(JSON)
    top_clients = Column(JSON)
    total = Column(Integer)
    date_since_total = Column(DateTime)
    ping_results = Column(JSON)
    
    def __init__(self):
        self.time_results_parsed = datetime.datetime.utcnow()
        self.last_hour = attacks_since('hours', 1)
        self.last_24_hrs = attacks_since('days', 1)
        self.last_week = attacks_since('days', 7)
        self.last_month = attacks_since('days', 30)
        self.total = total_attacks()
        self.total_attack_patterns = json.dumps(total_attack_patterns())
        self.top_clients = json.dumps(top_clients())
        self.ping_results = json.dumps(check_servers())
        self.top_asns = json.dumps(asn_count())




