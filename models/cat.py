from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
# from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY

Base = declarative_base()

class Cat(Base):
    """Table to hold all cat data """
    __tablename__ = 'cat'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    sex = Column(String(1))
    breed = Column(String)
    age_in_year = Column(Float)
    location = Column(String)
    notes = Column(String)
    weight_in_lbs = Column(Float)
    status = Column(String)
    photo_urls=Column(ARRAY(String))
    url=Column(String)

    __table_args__ = {'schema': 'spca_cat_adoption'}


class CatOnWebPage(Base):
    """Temp table used to store all cat data obtained from webscraping"""
    __tablename__ = 'cat_on_webpage'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    sex = Column(String(1))
    breed = Column(String)
    age_in_year = Column(Float)
    location = Column(String)
    notes = Column(String)
    weight_in_lbs = Column(Float)
    status = Column(String)
    photo_urls=Column(ARRAY(String))
    url=Column(String)

    def __repr__(self):
        return 'id:{}, sex:{}'.format(self.id, self.sex)

    __table_args__ = {'schema': 'spca_cat_adoption'}

