import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv


load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")


print(f"DEBUG - Database URL hai: {SQLALCHEMY_DATABASE_URL}")


if SQLALCHEMY_DATABASE_URL is None:
    raise ValueError("Error: .env file read nahi ho rahi hai ya DATABASE_URL nahi likha hai!")


engine = create_engine(SQLALCHEMY_DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()