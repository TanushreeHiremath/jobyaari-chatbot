import streamlit as st
import pandas as pd
from collections import defaultdict
import sys, os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from chatbot.groq_api import query_jobs_groq
DATA_PATH = os.path.join(os.path.dirname(__file__), '../data/jobyaari_jobs_cleaned.xlsx')
df = pd.read_excel(DATA_PATH)
job_knowledge_base = df.to_dict(orient="records")
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

# Streamlit
st.set_page_config(page_title="JobYaari Chatbot", layout="wide")
st.title("JobYaari Chatbot :)")
# Auto refresh every 2 minutes
st_autorefresh(interval=120000, key="job_refresh")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown("""
<style>
.stApp { background-color: #1E1E1E; color: white; }
input, .stTextInput>div>div>input { background-color: #2E2E2E; color: white; }
</style>
""", unsafe_allow_html=True)
def send_message():
    user_message = st.session_state.user_input.strip()
    if not user_message:
        return

    category = None
    for cat in jobs_by_category.keys():
        if cat.lower() in user_message.lower():
            category = cat
            break
    locations = set(job["location"].lower() for job in job_knowledge_base if job.get("location"))
    location = None
    for loc in locations:
        if loc in user_message.lower():
            location = loc
            break
    filtered_jobs = filter_jobs(category=category, location=location)
    if not filtered_jobs:
        bot_answer = "Sorry, no jobs found matching your query."
    else:
        bot_answer = query_jobs_groq(user_message, jobs_subset=filtered_jobs)

    st.session_state.chat_history.append({"user": user_message, "bot": bot_answer})
    st.session_state.user_input = ""
st.text_input("Type your message here:", key="user_input", on_change=send_message)
for chat in reversed(st.session_state.chat_history):
    st.markdown(f"""
    <div style='text-align: right; margin:10px 0;'>
        <span style='background-color:#2E86C1; color:white; padding:10px; border-radius:10px; display:inline-block'>{chat['user']}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: left; margin:10px 0;'>
        <span style='background-color:#555555; color:white; padding:10px; border-radius:10px; display:inline-block'>{chat['bot']}</span>
    </div>
    """, unsafe_allow_html=True)
st.markdown("---")  # horizontal separator
st.subheader("Job Summary")
st.write(f"Total jobs loaded: {len(job_knowledge_base)}")
categories = defaultdict(int)
for job in job_knowledge_base:
    categories[job.get("category", "N/A")] += 1
st.dataframe(pd.DataFrame(list(categories.items()), columns=["Category", "Job Count"]))

# show last updated time
st.markdown(f"*Last updated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}*")

