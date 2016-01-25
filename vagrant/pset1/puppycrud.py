from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from puppies import Base, Shelter, Puppy

engine = create_engine('sqlite:///puppyshelter.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

all_puppies = session.query(Puppy).order_by(Puppy.name)
for puppy in all_puppies:
    print puppy.name

young_puppies = session.query(Puppy).filter(Puppy.dateOfBirth > '2015-06-01').order_by(Puppy.dateOfBirth)
for puppy in young_puppies:
    print puppy.dateOfBirth

all_puppies_by_weight = session.query(Puppy).order_by(Puppy.weight)
for puppy in all_puppies_by_weight:
    print puppy.weight

all_puppies_grouped = session.query(Puppy).order_by(Puppy.shelter_id)
for puppy in all_puppies_grouped:
    print puppy.shelter.name
