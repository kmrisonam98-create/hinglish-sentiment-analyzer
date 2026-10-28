import streamlit as st
import pandas as pd
from transformers import pipeline
from sqlalchemy import create_engine, text


st.set_page_config(page_title="Hinglish Sentiment Analyzer", page_icon="🤖")
st.title("🤖 AI Hinglish Sentiment & Intent Analyzer")
st.write("Apna Hinglish text yahan type karein aur AI ka magic dekhein!")


@st.cache_resource
def load_ai_model():
    return pipeline("text-classification", model="cardiffnlp/twitter-xlm-roberta-base-sentiment", return_all_scores=False)

analyzer = load_ai_model()


@st.cache_resource
def init_connection():
    
    db_url = st.secrets["DATABASE_URL"]
    engine_conn = create_engine(db_url)
    
   
    with engine_conn.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id SERIAL PRIMARY KEY,
                text VARCHAR(500),
                sentiment VARCHAR(50),
                confidence FLOAT
            )
        '''))
        conn.commit()
    return engine_conn


engine = None
db_connected = False

try:
    engine = init_connection()
    db_connected = True
except Exception as e:
    st.warning("⚠️ Database connect nahi ho paya ya abhi setup nahi hai. Par AI Model chalega!")


user_input = st.text_area("Hinglish Text likhein:", placeholder="Bhai aaj toh mazza hi aa gaya!")

if st.button("Analyze Sentiment"):
    if user_input.strip() == "":
        st.error("Bhai pehle kuch text toh likho!")
    else:
        with st.spinner("AI Soch raha hai... Model first time thoda time le sakta hai..."):
           
            result = analyzer(user_input)[0]
            label_mapping = {"label_0": "Negative 😡", "label_1": "Neutral 😐", "label_2": "Positive 😄"}
            sentiment = label_mapping.get(result["label"], result["label"])
            confidence = round(result["score"] * 100, 2)

           
            st.success(f"**Sentiment:** {sentiment}")
            st.info(f"**Confidence:** {confidence}%")

            
            if db_connected and engine is not None:
                try:
                    with engine.connect() as conn:
                        conn.execute(text(
                            "INSERT INTO analysis_history (text, sentiment, confidence) VALUES (:t, :s, :c)"
                        ), {"t": user_input, "s": sentiment, "c": confidence})
                        conn.commit()
                except Exception as save_err:
                    st.error("Database mein save nahi ho paya, par analysis complete hai.")