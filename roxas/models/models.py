from sqlalchemy import Column, Integer, String, DateTime
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
    api_key = Column(String(64), nullable=False, unique=True)
    device_owners = Column(ARRAY(String()), nullable=False)
    allowed_users = Column(ARRAY(String()))
    returned_attributes = Column(ARRAY(String()))

    def __init__(self, name, description, api_key, device_owners, allowed_users=None, returned_attributes=None):
        self.name = name
        self.description = description
        self.api_key = api_key
        self.device_owners = device_owners
        self.allowed_users = allowed_users
        self.returned_attributes = returned_attributes
