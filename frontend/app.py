import streamlit as st
import pandas as pd
import plotly.express as px
from transformers import pipeline
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Hinglish Sentiment Analyzer", page_icon="🗣️", layout="wide")

if 'show_dashboard' not in st.session_state:
    st.session_state.show_dashboard = False

st.title("🗣️ Hinglish Sentiment & Intent Analyzer")
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

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📝 Analyze New Text")
    user_input = st.text_area("Hinglish Text Enter Karein:", height=150)
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        analyze_clicked = st.button("Analyze Text", use_container_width=True)
    with btn_col2:
        if st.button("📊 Show/Hide Dashboard", use_container_width=True):
            st.session_state.show_dashboard = not st.session_state.show_dashboard
            st.rerun()
    
    if analyze_clicked:
        if user_input.strip() == "":
            st.error("Bhai pehle kuch text toh likho!")
        else:
            with st.spinner("AI Soch raha hai..."):
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
                        st.error("Database mein save nahi ho paya.")

with col2:
    if st.session_state.show_dashboard:
        st.markdown("<h4 style='text-align: center;'>Overall Sentiment Distribution</h4>", unsafe_allow_html=True)
        
        if db_connected and engine is not None:
            try:
                df = pd.read_sql("SELECT sentiment FROM analysis_history", engine)
                
                if not df.empty:
                    sentiment_counts = df['sentiment'].value_counts().reset_index()
                    sentiment_counts.columns = ['Sentiment', 'Count']
                    
                    color_map = {
                        "Positive 😄": "#2E7D32",
                        "Negative 😡": "#D32F2F",
                        "Neutral 😐": "#78909C"
                    }
                    
                    fig = px.pie(
                        sentiment_counts, 
                        names='Sentiment', 
                        values='Count',
                        color='Sentiment',
                        color_discrete_map=color_map,
                        hole=0.45
                    )
                    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20))
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Pie chart ke liye abhi data nahi hai.")
            except Exception as e:
                st.error("Chart load karne mein error aaya.")
        else:
            st.warning("Database connected nahi hai, isliye chart nahi dikh raha.")

if st.session_state.show_dashboard:
    st.divider()
    
    col_hist, col_btn = st.columns([8, 2])
    with col_hist:
        st.subheader("📊 Analysis History")
    with col_btn:
        st.write("")
        st.button("🔄 Refresh Dashboard", use_container_width=True)

    if db_connected and engine is not None:
        try:
            df_history = pd.read_sql("SELECT text, sentiment, confidence FROM analysis_history ORDER BY id DESC LIMIT 10", engine)
            if not df_history.empty:
                st.dataframe(df_history, use_container_width=True)
            else:
                st.info("Abhi tak koi data nahi hai. Upar kuch analyze karein!")
        except Exception as e:
            st.error("History load karne mein error aaya.")