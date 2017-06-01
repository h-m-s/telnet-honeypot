#!/usr/bin/python3
"""
Defines attacker objects for the db.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from models.base import BaseModel, Base
from ipwhois import IPWhois

class Attacker(BaseModel, Base):
    """
    Class definition for attackers.
    Stores the ip and ASN information for attackers, and a count
    to increment.
    """
    __tablename__ = 'attackers'
    ip = Column(postgresql.INET, primary_key=True)
    count = Column(Integer, nullable=False)
    asn = Column(Integer)
    asn_country_code = Column(String)

    def __init__(self, ip):
        self.ip = ip
        self.count = 1
        self.asn, self.asn_country_code = self.get_attacker_asn(ip)

    def get_attacker_asn(self, ip):
        whois = IPWhois(ip)
        results = whois.lookup_whois()
        return(results['asn'].split(' ')[0], results['asn_country_code'])
