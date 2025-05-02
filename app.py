"""
app.py – Streamlit chat wrapper for Mentor
Run with:  streamlit run app.py
"""

import streamlit as st
from boot import memory_manager, llm_client  # <-- your existing wiring
from src.mentor import Mentor

# ---------- 1. initialise once ----------
if "mentor" not in st.session_state:
    st.session_state.mentor = Mentor(memory_manager, llm_client, user_id="u42")
if "history" not in st.session_state:
    st.session_state.history = []  # [(role, text), ...]

mentor: Mentor = st.session_state.mentor

# ---------- 2. sidebar ----------
st.sidebar.title("Mentor")
st.sidebar.markdown(
    """
**Tips**
- The mentor *remembers* what you say.
- Ask follow-up questions; the answers shape its memory.
- Use `⚙️ Reset Memory` to start fresh (dev only).
"""
)

if st.sidebar.button("⚙️ Reset Memory"):
    st.session_state.history = []
    st.rerun()

# ---------- 3. main chat ----------
st.title("🧑‍🏫 Mentor")

for role, text in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)

if prompt := st.chat_input("Ask your mentor…"):
    # show user msg immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.history.append(("user", prompt))

    # get mentor reply
    with st.chat_message("assistant"):
        response = st.write_stream(mentor.stream_reply(prompt))
    st.session_state.history.append(("assistant", response))
