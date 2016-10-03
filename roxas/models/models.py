from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime

from roxas import db

class Test(db.Model):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    datetime_created = Column(DateTime)

    def __init__(self, name):
        self.name = name
        self.datetime_created = datetime.now()

    def __repr__(self):
        return '<id {}>'.format(self.id)

class Device(db.Model):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(String(500), nullable=False)
    created_by = Column(String(64), nullable=False)
    api_key = Column(String(64), nullable=False, unique=True)
    device_owners_users = Column(ARRAY(String()))
    device_owners_groups = Column(ARRAY(String()))
    accessible_by_users = Column(ARRAY(String()))
    accessible_by_groups = Column(ARRAY(String()))
    enabled = Column(Boolean, default=True)

    def __init__(self, name, description, created_by, api_key, device_owners_users, device_owners_groups, accessible_by_users, accessible_by_groups):
        self.name = name
        self.description = description
        self.created_by = created_by
        self.api_key = api_key
        self.device_owners_users = device_owners_users
        self.device_owners_groups = device_owners_groups
        self.accessible_by_users = accessible_by_users
        self.accessible_by_groups = accessible_by_groups
        enabled = True

class NFC(db.Model):
    __tablename__ = "nfcs"

    id = Column(Integer, primary_key=True)
    serial_number = Column(String(64), nullable=False, unique=True)
    current_rolling_key = Column(String(64), nullable=False)
    next_rolling_key = Column(String(64))
    old_rolling_key = Column(String(64))
    verified = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)

    def __init__(self, serial_number, rolling_key):
        self.serial_number = serial_number
        self.current_rolling_key = rolling_key
        verified = True
        enabled = True

