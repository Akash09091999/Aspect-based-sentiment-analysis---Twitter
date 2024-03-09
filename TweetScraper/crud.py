from sqlalchemy import create_engine
from models import Base
# from config import DATABASE_URI
from sqlalchemy.orm import sessionmaker

# DATABASE_URI to connect database
# Scheme: "postgres+psycopg2://<USERNAME>:<PASSWORD>@<IP_ADDRESS>:<PORT>/<DATABASE_NAME>"
DATABASE_URI = "postgres+psycopg2://postgres:postgres@localhost:5432/tweetdb"

engine = create_engine(DATABASE_URI)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
