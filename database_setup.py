import os
import sys
import datetime
import json

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    items = relationship("Item")

    @property
    def serialize(self):
        # Return object data in easily serializeable format
        return {

            'id': self.id,
            'items': [item.serialize for item in self.items],
            'name': self.name

        }


class Item(Base):
    __tablename__ = 'item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    picture = Column(String(250), nullable=True)
    category_id = Column(Integer, ForeignKey('category.id'))
    date_creation = Column(DateTime(timezone=True),
                           server_default=func.now())
    date_update = Column(DateTime(timezone=True),
                         server_default=func.now())
    category = relationship(Category, back_populates='items')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        # Return object data in easily serializeable format
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            # 'date_update' : self.date_update,
            'picture': self.picture
        }


engine = create_engine('sqlite:///catalogitems.db')
Base.metadata.create_all(engine)
