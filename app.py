import streamlit as st
import praw
import os
import google.generativeai as genai
import json
import re
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF

# ====== CONFIG ======
st.set_page_config(page_title="Reddit Persona Generator", layout="wide")
DATA_DIR = "user_persona"

# ====== Sidebar Input ======
st.sidebar.title("🔍 Reddit Persona Generator")
username_input = st.sidebar.text_input("Enter Reddit username or profile URL", "")
generate_button = st.sidebar.button("🚀 Generate Persona")

# ====== Configure Gemini ======
genai.configure(api_key=st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "")

# ====== Prompt ======
prompt = """
You are an expert persona profiler and product designer.

Based on the Reddit user's posts and comments, generate a detailed structured persona in **JSON format** with the following fields:

{
  "full_name": "Generated name (optional)",
  "age_group": "e.g., 25-34",
  "occupation": "Inferred profession or background",
  "location": "Inferred location or leave as 'Unknown'",
  "tone_of_writing": "Casual, formal, sarcastic, etc.",
  "dominant_emotions": ["emotion1", "emotion2"],
  "personality_traits": {
    "Introvert vs Extrovert": "Extrovert",
    "Thinking vs Feeling": "Thinking",
    "Judging vs Perceiving": "Judging",
    "Intuition vs Sensing": "Intuition"
  },
  "motivations": [
    "List key motivators from content"
  ],
  "goals": [
    "List user’s likely goals"
  ],
  "frustrations": [
    "List pain points or frustrations"
  ],
  "quotes": [
    "Include up to 3 notable quotes that reflect the user’s personality"
  ]
}

- Format the response as raw JSON (no markdown).
- Be concise but expressive.
- Assume this will be used in a UI for product design and personalization.

Only return the JSON. No extra commentary.
"""

# === Extract and Clean ===
def extract_username(input_text):
    raw = input_text.strip()
    if "reddit.com/user/" in raw:
        return raw.split("/")[-2]
    elif raw.startswith("u/"):
        return raw[2:]
    return raw

def clean_json_response(response):
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:].strip()
    elif response.startswith("```"):
        response = response[3:].strip()
    if response.endswith("```"):
        response = response[:-3].strip()
    return response

@st.cache_resource
def get_reddit_instance():
    return praw.Reddit(
        client_id=st.secrets["REDDIT_CLIENT_ID"],
        client_secret=st.secrets["REDDIT_CLIENT_SECRET"],
        user_agent="PersonaGenReadOnly"
    )

def fetch_user_activity(username, post_limit=30, comment_limit=30):
    reddit = get_reddit_instance()
    user = reddit.redditor(username)
    content = []
    try:
        for submission in user.submissions.new(limit=post_limit):
            content.append(f"[POST] {submission.title.strip()} — {submission.selftext.strip()[:300]}")
        for comment in user.comments.new(limit=comment_limit):
            content.append(f"[COMMENT] {comment.body.strip()[:300]}")
    except Exception as e:
        st.error(f"❌ Error fetching Reddit data: {e}")
    return content

def generate_persona(text):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    response = model.generate_content([prompt, text])
    return clean_json_response(response.text)

def sanitize_username(raw_input):
    raw = raw_input.strip()
    if "reddit.com/user/" in raw:
        return raw.split("/")[-2]
    if raw.startswith("u/"):
        return raw[2:]
    if raw.endswith("_persona.json"):
        return raw.replace("_persona.json", "")
    if raw.endswith(".json"):
        return raw.replace(".json", "")
    return raw

def load_persona_json(username):
    path = os.path.join(DATA_DIR, f"{username}_persona.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ===== Main Dashboard =====
st.title("🧠 Reddit Persona Generator")
persona_data = None

if generate_button and username_input:
    with st.spinner("Scraping Reddit and analyzing persona..."):
        uname = extract_username(username_input)
        activity = fetch_user_activity(uname)
        if activity:
            raw_text = "\n\n".join(activity)
            try:
                json_str = generate_persona(raw_text)
                try:
                    parsed = json.loads(json_str)
                    persona_data = parsed.get("persona", parsed)
                    with open(os.path.join(DATA_DIR, f"{uname}_persona.json"), "w", encoding="utf-8") as f:
                        json.dump(persona_data, f, indent=2)
                    st.session_state["persona"] = persona_data
                    st.success("✅ Persona generated successfully!")
                except json.JSONDecodeError:
                    st.error("❌ Could not parse Gemini output. Check raw JSON below:")
                    st.code(json_str, language="json")
            except Exception as e:
                st.error(f"❌ Gemini Error: {e}")
        else:
            st.warning("⚠️ No user activity found on Reddit.")

# ==== Load Persona View Mode ====
raw_input = username_input
username = sanitize_username(raw_input)
data = st.session_state.get("persona") or load_persona_json(username) if username else None

if data:
    col1, col2 = st.columns([1, 2])

    # === Left Column: Profile ===
    with col1:
        st.image("https://i.ibb.co/VVTFgwp/person-placeholder.png", width=220)
        st.markdown(f"## {data.get('full_name', username).capitalize()}")
        st.markdown(f"**Age Group:** {data.get('age_group', 'Unknown')}")
        st.markdown(f"**Occupation:** {data.get('occupation', 'Unknown')}")
        st.markdown(f"**Location:** {data.get('location', 'Unknown')}")
        st.markdown(f"**Writing Tone:** {data.get('tone_of_writing', 'Unknown')}")
        st.markdown(f"**Dominant Emotions:** {', '.join(data.get('dominant_emotions', []))}")

    # === Right Column: Tabs ===
    with col2:
        tabs = st.tabs(["🧠 Personality", "🚀 Motivations", "🎯 Goals", "😠 Frustrations", "💬 Quotes"])

        with tabs[0]:
            st.markdown("### Personality Traits")
            traits = data.get("personality_traits", {})
            for trait, value in traits.items():
                st.write(f"**{trait}:**")
                st.progress(100 if value.lower() in trait.lower() else 50)

        with tabs[1]:
            st.markdown("### Key Motivations")
            for item in data.get("motivations", []):
                st.markdown(f"- {item}")

        with tabs[2]:
            st.markdown("### Goals")
            for item in data.get("goals", []):
                st.markdown(f"- {item}")

        with tabs[3]:
            st.markdown("### Frustrations")
            for item in data.get("frustrations", []):
                st.markdown(f"- {item}")

        with tabs[4]:
            st.markdown("### Notable Quotes")
            for quote in data.get("quotes", []):
                st.markdown(f"> *{quote}*")

    st.sidebar.download_button(
        label="📥 Download Persona JSON",
        data=json.dumps(data, indent=2),
        file_name=f"{username}_persona.json",
        mime="application/json"
    )
else:
    if raw_input:
        st.error(f"❌ Persona not found for '{username}'. Make sure the file exists at: `{DATA_DIR}/{username}_persona.json`")
    else:
        st.info("Enter a Reddit username to load or generate the persona.")
