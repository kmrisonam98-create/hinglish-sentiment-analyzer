from fastapi import FastAPI, Depends
from pydantic import BaseModel
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from transformers import pipeline

# 1. Database Setup (Tables create karna)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 2. AI Model Load Karna
print("AI Model Load ho raha hai, kripya thoda wait karein...")
# Naya aur zyada reliable model jo mixed language samajhta hai
sentiment_pipeline = pipeline("text-classification", model="cardiffnlp/twitter-xlm-roberta-base-sentiment")
print("🚀 Model successfully load ho gaya!")

# 3. Database Connection Pipe
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 4. Pydantic Model (Input Data Check)
class AnalyzeRequest(BaseModel):
    text: str

# 5. AI Logic Function (Bulletproof Version)
def analyze_hinglish(text: str):
    text_lower = text.lower()
    
    # Intent Logic (Smart Question Detection)
    if "?" in text_lower or text_lower.startswith("kya ") or text_lower.startswith("kaise "):
        intent = "Question"
    else:
        intent = "Statement/Feedback"
        
    try:
        # AI Sentiment Prediction
        ai_result = sentiment_pipeline(text)[0]
        
        # Label ko string banakar sab lowercase kar diya taaki mismatch na ho
        label = str(ai_result.get('label', '')).lower()
        
        # Spy/Debug print taaki hum terminal mein asli output dekh sakein
        print(f"🧠 AI Debug -> Label aayi hai: '{label}'")
        
        # Bulletproof Mapping: Agar label mein '2' ya 'pos' hai, toh Positive
        if '2' in label or 'pos' in label:
            sentiment = "Positive 😃"
        elif '0' in label or 'neg' in label:
            sentiment = "Negative 😡"
        else:
            sentiment = "Neutral 😐"
            
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        sentiment = "Neutral 😐" # Agar AI fail ho jaye, toh project crash na ho
        
    return {"sentiment": sentiment, "intent": intent}


# ----------------- API ENDPOINTS -----------------

# GET: Root Endpoint
@app.get("/")
def read_root():
    return {"message": "Namaste! Hinglish Analyzer Backend is Running."}

# POST: Text Analyze aur Save
@app.post("/analyze")
def analyze_text(request: AnalyzeRequest, db: Session = Depends(get_db)):
    
    # NLP logic se result nikala
    result = analyze_hinglish(request.text)
    
    # Database Table ka naya record banaya
    db_record = models.AnalysisHistory(
        original_text=request.text,
        sentiment=result["sentiment"],
        intent=result["intent"]
    )
    
    # Database mein save kiya
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return {
        "id": db_record.id,
        "original_text": db_record.original_text,
        "analysis": result,
        "message": "Data successfully AI se analyze ho kar Database mein save ho gaya! 🚀"
    }

# GET: History Endpoint (Dashboard Chart ke liye)
@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    # Database se aakhri 50 records nikalna
    records = db.query(models.AnalysisHistory).order_by(models.AnalysisHistory.id.desc()).limit(50).all()
    return {"history": records}