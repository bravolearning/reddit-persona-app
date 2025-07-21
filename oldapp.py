import os
import json
import streamlit as st

# === CONFIG ===
DATA_DIR = "user_persona"

# === Function: Sanitize Input ===
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

# === Function: Load Persona JSON ===
def load_persona_json(username):
    path = os.path.join(DATA_DIR, f"{username}_persona.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# === Streamlit UI ===
st.set_page_config(page_title="Reddit Persona", layout="wide")
st.title("🧠 Reddit Persona Profile")

# Input & cleaning
raw_input = st.sidebar.text_input("Enter Reddit username", "")
username = sanitize_username(raw_input)
data = load_persona_json(username) if username else None

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

    # === Right Column: Tabs for Detailed Sections ===
    with col2:
        tabs = st.tabs(["🧠 Personality", "🚀 Motivations", "🎯 Goals", "😠 Frustrations", "💬 Quotes"])

        # Personality Sliders
        with tabs[0]:
            st.markdown("### Personality Traits")
            traits = data.get("personality_traits", {})
            for trait, value in traits.items():
                st.write(f"**{trait}:**")
                st.progress(100 if value.lower() in trait.lower() else 50)

        # Motivations
        with tabs[1]:
            st.markdown("### Key Motivations")
            for item in data.get("motivations", []):
                st.markdown(f"- {item}")

        # Goals
        with tabs[2]:
            st.markdown("### Goals")
            for item in data.get("goals", []):
                st.markdown(f"- {item}")

        # Frustrations
        with tabs[3]:
            st.markdown("### Frustrations")
            for item in data.get("frustrations", []):
                st.markdown(f"- {item}")

        # Quotes
        with tabs[4]:
            st.markdown("### Notable Quotes")
            for quote in data.get("quotes", []):
                st.markdown(f"> *{quote}*")

    # Download
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
        st.info("Enter a Reddit username to load the persona.")
