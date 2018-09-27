import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

# Abuser class to insert people abusing the bugreporting feature
class Abuser(Base):
	__tablename__ = 'abusers'
	id = Column(Integer, primary_key = True)
	discord_id = Column(String, nullable = False)


# Entry class for voice-related giveaway entries
class Entry(Base):
	__tablename__ = 'entries'
	# Table column definitions
	id = Column(Integer, primary_key = True)
	discord_id = Column(String, nullable = False)
	score = Column(Integer, nullable = False)

# EventMessage class for stuff_happening messages
class EventMessage(Base):
	__tablename__ = 'message'
	id = Column(Integer, primary_key = True)
	token = Column(String, nullable = False)
	content = Column(String, nullable = False)
	image_url = Column(String, nullable = True)
	position = Column(Integer, nullable = False)

# Giveaway class to keep track of community giveaways
class Giveaway(Base):
	__tablename__ = 'giveaway'
	id = Column(Integer, primary_key = True)
	discord_id = Column(String, nullable = False)

# Create the engine to the sqlite database
engine = create_engine('sqlite:///database/database.sqlite')

# Handles the creation of tables (if none exist etc.)
Base.metadata.create_all(engine)
