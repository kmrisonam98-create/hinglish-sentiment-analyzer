from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import datetime

# Ye hamari Table ka design (schema) hai
class AnalysisHistory(Base):
    __tablename__ = "analysis_history"  # Database mein is naam se table banegi

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(String, index=True)
    sentiment = Column(String)
    intent = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)