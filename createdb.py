import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabledef import *

engine = create_engine('sqlite:///users.db', echo=True)

# create a Session
Session = sessionmaker(bind=engine)
session = Session()

user = User("admin","password","ducnguyen17199@gmail.com")
session.add(user)

user = User("sampleflask", "flask", "flaskappsampledc@gmail.com")
session.add(user)
# commit the record the database
session.commit()
