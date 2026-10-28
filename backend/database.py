import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 1. .env file se secret data load karo
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# --- DEBUGGING LINE (Check karne ke liye ki URL aa raha hai ya nahi) ---
print(f"DEBUG - Database URL hai: {SQLALCHEMY_DATABASE_URL}")

# --- SAFETY CHECK ---
if SQLALCHEMY_DATABASE_URL is None:
    raise ValueError("Error: .env file read nahi ho rahi hai ya DATABASE_URL nahi likha hai!")

# 2. Engine banao 
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Session banao
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class
Base = declarative_base()