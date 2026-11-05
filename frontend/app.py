import streamlit as st
import pandas as pd
import plotly.express as px
from transformers import pipeline
from sqlalchemy import create_engine, text
import hashlib

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
                confidence FLOAT,
                username VARCHAR(50)
            )
        '''))
        try:
            conn.execute(text("ALTER TABLE analysis_history ADD COLUMN username VARCHAR(50)"))
        except:
            pass
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
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
    st.warning("Database connection error.")

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.sidebar.title("🔐 User Account")

if not st.session_state.logged_in:
    st.info("App use karne ke liye pehle left sidebar se Login ya Sign Up karein.")
    menu = ["Login", "Sign Up"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Sign Up":
        new_user = st.sidebar.text_input("New Username")
        new_password = st.sidebar.text_input("New Password", type='password')
        if st.sidebar.button("Create Account"):
            if new_user and new_password:
                if db_connected and engine is not None:
                    try:
                        with engine.connect() as conn:
                            hashed_pswd = make_hashes(new_password)
                            conn.execute(text(
                                "INSERT INTO users (username, password_hash) VALUES (:u, :p)"
                            ), {"u": new_user, "p": hashed_pswd})
                            conn.commit()
                            st.sidebar.success("Account created! Ab login karein.")
                    except Exception as e:
                        st.sidebar.error("Username already exists.")
            else:
                st.sidebar.warning("Username aur password zaroori hai.")

    elif choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Login"):
            if db_connected and engine is not None:
                with engine.connect() as conn:
                    result = conn.execute(text(
                        "SELECT password_hash FROM users WHERE username = :u"
                    ), {"u": username}).fetchone()
                    
                    if result and check_hashes(password, result[0]):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.sidebar.success(f"Welcome {username}!")
                        st.rerun()
                    else:
                        st.sidebar.error("Galat username ya password.")

else:
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Analyze New Text")
        user_text = st.text_area("Hinglish Text Enter Karein:", value="", placeholder="Apna text yahan likhein...")

        if st.button("Analyze Text"):
            if user_text.strip() == "":
                st.error("Pehle kuch text toh likho!")
            else:
                with st.spinner("AI Soch raha hai..."):
                    result = analyzer(user_text)[0]
                    label_mapping = {"label_0": "Negative 😡", "label_1": "Neutral 😐", "label_2": "Positive 😄"}
                    sentiment = label_mapping.get(result["label"], result["label"])
                    confidence = round(result["score"] * 100, 2)

                    st.success("Analysis Complete & Saved!")
                    st.write(f"**Sentiment:** {sentiment}")
                    st.write(f"**Confidence:** {confidence}%")

                    if db_connected and engine is not None:
                        try:
                            with engine.connect() as conn:
                                conn.execute(text(
                                    "INSERT INTO analysis_history (text, sentiment, confidence, username) VALUES (:t, :s, :c, :u)"
                                ), {"t": user_text, "s": sentiment, "c": confidence, "u": st.session_state.username})
                                conn.commit()
                        except Exception as save_err:
                            st.error("Database mein save nahi ho paya.")

    st.markdown("---")
    st.subheader("📊 Analysis Dashboard")

    if st.button("Refresh Dashboard"):
        if db_connected and engine is not None:
            try:
                with engine.connect() as conn:
                    query = text("SELECT id, text, sentiment, confidence FROM analysis_history WHERE username = :u ORDER BY id DESC")
                    df = pd.read_sql(query, conn, params={"u": st.session_state.username})
                
                if not df.empty:
                    with col2:
                        def fix_sentiment_name(val):
                            val_str = str(val).lower()
                            if 'positive' in val_str: return 'Positive 😄'
                            if 'negative' in val_str: return 'Negative 😡'
                            if 'neutral' in val_str: return 'Neutral 😐'
                            return val
                            
                        df['sentiment'] = df['sentiment'].apply(fix_sentiment_name)
                        
                        all_categories = pd.DataFrame({'Sentiment': ['Positive 😄', 'Negative 😡', 'Neutral 😐']})
                        sentiment_counts = df['sentiment'].value_counts().reset_index()
                        sentiment_counts.columns = ['Sentiment', 'Count']
                        
                        sentiment_counts = pd.merge(all_categories, sentiment_counts, on='Sentiment', how='left').fillna(0)
                        
                        color_map = {
                            'Positive 😄': 'green', 
                            'Negative 😡': 'red', 
                            'Neutral 😐': 'gray'
                        }
                        
                        fig = px.pie(
                            sentiment_counts, 
                            values='Count', 
                            names='Sentiment', 
                            title="Overall Sentiment Distribution", 
                            color='Sentiment',
                            color_discrete_map=color_map
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.write("**Recent Analysis History:**")
                    st.dataframe(df[['id', 'text', 'sentiment', 'confidence']], use_container_width=True)
                else:
                    st.info("Abhi tak koi data save nahi hua hai. Pehle kuch text analyze karein.")
            except Exception as e:
                st.error("Dashboard load karne mein error aaya.")
        else:
            st.warning("Database connected nahi hai.")