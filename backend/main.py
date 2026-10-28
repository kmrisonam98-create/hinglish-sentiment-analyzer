from fastapi import FastAPI, Depends
from pydantic import BaseModel
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from transformers import pipeline


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


print("AI Model Load ho raha hai, kripya thoda wait karein...")

sentiment_pipeline = pipeline("text-classification", model="cardiffnlp/twitter-xlm-roberta-base-sentiment")
print("🚀 Model successfully load ho gaya!")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AnalyzeRequest(BaseModel):
    text: str


def analyze_hinglish(text: str):
    text_lower = text.lower()
    
    
    if "?" in text_lower or text_lower.startswith("kya ") or text_lower.startswith("kaise "):
        intent = "Question"
    else:
        intent = "Statement/Feedback"
        
    try:
        
        ai_result = sentiment_pipeline(text)[0]
        
        
        label = str(ai_result.get('label', '')).lower()
        
       
        print(f"🧠 AI Debug -> Label aayi hai: '{label}'")
        
     
        if '2' in label or 'pos' in label:
            sentiment = "Positive 😃"
        elif '0' in label or 'neg' in label:
            sentiment = "Negative 😡"
        else:
            sentiment = "Neutral 😐"
            
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        sentiment = "Neutral 😐" 
        
    return {"sentiment": sentiment, "intent": intent}





@app.get("/")
def read_root():
    return {"message": "Namaste! Hinglish Analyzer Backend is Running."}


@app.post("/analyze")
def analyze_text(request: AnalyzeRequest, db: Session = Depends(get_db)):
    
    
    result = analyze_hinglish(request.text)
    
    
    db_record = models.AnalysisHistory(
        original_text=request.text,
        sentiment=result["sentiment"],
        intent=result["intent"]
    )
    
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return {
        "id": db_record.id,
        "original_text": db_record.original_text,
        "analysis": result,
        "message": "Data successfully AI se analyze ho kar Database mein save ho gaya! 🚀"
    }


@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    
    records = db.query(models.AnalysisHistory).order_by(models.AnalysisHistory.id.desc()).limit(50).all()
    return {"history": records}