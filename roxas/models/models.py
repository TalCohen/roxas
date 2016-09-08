from sqlalchemy import Column, Integer, String, DateTime
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
