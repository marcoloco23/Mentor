"""
app.py – Streamlit chat wrapper for Mentor
Run with:  streamlit run app.py
"""

import streamlit as st
from boot import memory_manager, llm_client  # <-- your existing wiring
from src.mentor import Mentor
from typing import Optional

# ---------- 1. initialise once ----------
if "mentor" not in st.session_state:
    st.session_state.mentor = Mentor(memory_manager, llm_client, user_id="u42")
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "history" not in st.session_state:
    st.session_state.history = []  # [(role, text), ...]

mentor: Mentor = st.session_state.mentor
user_id = mentor.user_id

# ---------- 2. sidebar: thread selection ----------
st.sidebar.title("Mentor")
st.sidebar.markdown(
    """
**Tips**
- The mentor *remembers* what you say.
- Ask follow-up questions; the answers shape its memory.
- Use `⚙️ Reset Memory` to start fresh (dev only).
"""
)

threads = memory_manager.list_threads(user_id)
thread_labels = [f"Thread {i+1}: {tid[:8]}" for i, tid in enumerate(threads)]
thread_options = ["➕ New Thread"] + thread_labels
selected = st.sidebar.radio("Conversation Threads", thread_options, key="thread_radio")

if selected == "➕ New Thread":
    st.session_state.current_thread_id = None
    st.session_state.history = []
else:
    idx = thread_labels.index(selected)
    thread_id = threads[idx]
    st.session_state.current_thread_id = thread_id
    # Load thread history for display
    thread_msgs = memory_manager.get_thread(thread_id) or []
    st.session_state.history = [(msg["role"], msg["content"]) for msg in thread_msgs]

if st.sidebar.button("⚙️ Reset Memory"):
    st.session_state.history = []
    st.session_state.current_thread_id = None
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
        response = st.write_stream(
            mentor.stream_reply(prompt, thread_id=st.session_state.current_thread_id)
        )
    st.session_state.history.append(("assistant", response))

    # If a new thread, get the thread_id from the last message
    if st.session_state.current_thread_id is None:
        # Find the latest thread for this user (should be the most recent)
        threads = memory_manager.list_threads(user_id)
        if threads:
            st.session_state.current_thread_id = threads[-1]
