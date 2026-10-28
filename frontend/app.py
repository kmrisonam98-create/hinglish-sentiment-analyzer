import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_ANALYZE_URL = "http://127.0.0.1:8000/analyze"
API_HISTORY_URL = "http://127.0.0.1:8000/history"

st.set_page_config(page_title="Hinglish Analyzer", layout="wide")
st.title("🗣️ Hinglish Sentiment & Intent Analyzer")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Analyze New Text")
    user_text = st.text_area("Hinglish Text Enter Karein:")

    if st.button("Analyze Text"):
        if user_text:
            payload = {"text": user_text}
            try:
                response = requests.post(API_ANALYZE_URL, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Analysis Complete & Saved!")
                    st.write(f"**Sentiment:** {data['analysis']['sentiment']}")
                    st.write(f"**Intent:** {data['analysis']['intent']}")
                else:
                    st.error("Backend ne error diya!")
            except requests.exceptions.ConnectionError:
                st.error("Backend se connect nahi ho pa raha. Kya backend server on hai?")

st.markdown("---")
st.subheader("📊 Analysis Dashboard")

if st.button("Refresh Dashboard"):
    try:
        res = requests.get(API_HISTORY_URL)
        if res.status_code == 200:
            history_data = res.json()["history"]
            
            if len(history_data) > 0:
                df = pd.DataFrame(history_data)
                
                with col2:
                    sentiment_counts = df['sentiment'].value_counts().reset_index()
                    sentiment_counts.columns = ['Sentiment', 'Count']
                    
                    fig = px.pie(sentiment_counts, values='Count', names='Sentiment', 
                                 title="Overall Sentiment Distribution", 
                                 color='Sentiment',
                                 color_discrete_map={'Positive 😃':'green', 'Negative 😡':'red', 'Neutral 😐':'gray'})
                    st.plotly_chart(fig, use_container_width=True)
                
                st.write("**Recent Analysis History:**")
                df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime("%Y-%m-%d %H:%M")
                st.dataframe(df[['id', 'original_text', 'sentiment', 'intent', 'created_at']], use_container_width=True)
            else:
                st.info("Abhi tak koi data save nahi hua hai. Pehle kuch text analyze karein.")
    except Exception as e:
        st.error("Dashboard load karne mein error aaya. Kya backend on hai?")