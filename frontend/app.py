import streamlit as st
import pandas as pd
import plotly.express as px
from transformers import pipeline
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Hinglish Analyzer", layout="wide")
st.title("🗣️ Hinglish Sentiment & Intent Analyzer")

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

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📝 Analyze New Text")
    user_text = st.text_area("Hinglish Text Enter Karein:", "Bhai ye project toh ekdum mast hai!")

    if st.button("Analyze Text"):
        if user_text.strip() == "":
            st.error("Bhai pehle kuch text toh likho!")
        else:
            with st.spinner("AI Soch raha hai..."):
                result = analyzer(user_text)[0]
                label_mapping = {"label_0": "Negative 😡", "label_1": "Neutral 😐", "label_2": "Positive 😄"}
                sentiment = label_mapping.get(result["label"], result["label"])
                confidence = round(result["score"] * 100, 2)

                st.success("✅ Analysis Complete & Saved!")
                st.write(f"**Sentiment:** {sentiment}")
                st.write(f"**Confidence:** {confidence}%")

                if db_connected and engine is not None:
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(
                                "INSERT INTO analysis_history (text, sentiment, confidence) VALUES (:t, :s, :c)"
                            ), {"t": user_text, "s": sentiment, "c": confidence})
                            conn.commit()
                    except Exception as save_err:
                        st.error("Database mein save nahi ho paya.")

st.markdown("---")
st.subheader("📊 Analysis Dashboard")

if st.button("🔄 Refresh Dashboard"):
    if db_connected and engine is not None:
        try:
            df = pd.read_sql("SELECT id, text, sentiment, confidence FROM analysis_history ORDER BY id DESC", engine)
            
            if not df.empty:
                with col2:
                    sentiment_counts = df['sentiment'].value_counts().reset_index()
                    sentiment_counts.columns = ['Sentiment', 'Count']
                    
                    color_map = {
                        "Positive 😄": "#2E7D32",
                        "Negative 😡": "#D32F2F",
                        "Neutral 😐": "#78909C"
                    }
                    
                    fig = px.pie(
                        sentiment_counts, 
                        values='Count', 
                        names='Sentiment', 
                        title="Overall Sentiment Distribution", 
                        color='Sentiment',
                        color_discrete_map=color_map,
                        hole=0.45
                    )
                    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
                
                st.write("**Recent Analysis History:**")
                st.dataframe(df[['id', 'text', 'sentiment', 'confidence']], use_container_width=True)
            else:
                st.info("Abhi tak koi data save nahi hua hai. Pehle kuch text analyze karein.")
        except Exception as e:
            st.error("Dashboard load karne mein error aaya.")
    else:
        st.warning("Database connected nahi hai.")