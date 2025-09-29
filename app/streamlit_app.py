import streamlit as st
from streamlit_autorefresh import st_autorefresh
from jobyaari_scraper import JobYaariScraper
import pandas as pd
from collections import defaultdict
import sys
import os

# Optional: Add parent folder to sys.path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from chatbot.groq_api import query_jobs_groq

# Auto-refresh every 60 seconds
st_autorefresh(interval=60000, key="job_refresh")

# Page setup
st.set_page_config(page_title="Live JobYaari Jobs & Chatbot", layout="wide")
st.title("📢 Live JobYaari Jobs & Chatbot")

# Run scraper
scraper = JobYaariScraper()
df = scraper.scrape()

if df is not None and not df.empty:
    st.write(f"Total jobs found: {len(df)}")
    st.dataframe(df)
else:
    st.warning("No jobs found. Try refreshing or check the website.")

# --- Chatbot Section ---
st.markdown("---")
st.subheader("JobYaari Chatbot 🤖")

# Save a cleaned Excel copy for chatbot knowledge base
data_path_cleaned = os.path.join(os.path.dirname(__file__), '../data/jobyaari_jobs_cleaned.xlsx')
os.makedirs(os.path.dirname(data_path_cleaned), exist_ok=True)
if df is not None:
    df.to_excel(data_path_cleaned, index=False)

# Load knowledge base
job_knowledge_base = df.to_dict(orient="records") if df is not None else []

jobs_by_category = defaultdict(list)
for job in job_knowledge_base:
    category = job.get("category", "N/A").strip().title()
    jobs_by_category[category].append(job)

def filter_jobs(category=None, location=None, min_salary=None):
    filtered = job_knowledge_base

    if category:
        category = category.strip().title()
        filtered = jobs_by_category.get(category, [])

    if location:
        filtered = [job for job in filtered if location.lower() in job.get("location", "").lower()]

    if min_salary:
        def parse_salary(s):
            try:
                return int(''.join(filter(str.isdigit, str(s))))
            except:
                return 0
        filtered = [job for job in filtered if parse_salary(job.get("salary", 0)) >= min_salary]

    return filtered

# Custom CSS for dark theme
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1E1E1E;
        color: white;
    }
    input, .stTextInput>div>div>input {
        background-color: #2E2E2E;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def send_message():
    user_message = st.session_state.user_input
    if user_message:
        # Detect category from message
        category = None
        for cat in jobs_by_category.keys():
            if cat.lower() in user_message.lower():
                category = cat
                break

        # Detect location from message
        locations = set(job["location"].lower() for job in job_knowledge_base)
        location = None
        for loc in locations:
            if loc in user_message.lower():
                location = loc
                break

        # Filter jobs
        filtered_jobs = filter_jobs(category=category, location=location)
        if not filtered_jobs:
            bot_answer = "Sorry, no jobs found matching your query."
        else:
            bot_answer = query_jobs_groq(user_message, jobs_subset=filtered_jobs)

        st.session_state.chat_history.append({"user": user_message, "bot": bot_answer})
        st.session_state.user_input = ""

# Input box
st.text_input("Type your message here:", key="user_input", on_change=send_message)

# Display chat history
for chat in reversed(st.session_state.chat_history):
    st.markdown(
        f"<div style='text-align: right; margin:10px 0;'>"
        f"<span style='background-color:#2E86C1; color:white; padding:10px; border-radius:10px; display:inline-block'>{chat['user']}</span>"
        f"</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div style='text-align: left; margin:10px 0;'>"
        f"<span style='background-color:#555555; color:white; padding:10px; border-radius:10px; display:inline-block'>{chat['bot']}</span>"
        f"</div>",
        unsafe_allow_html=True
    )
