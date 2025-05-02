"""
app.py – Streamlit chat wrapper for Mentor
Run with:  streamlit run app.py
"""

from __future__ import annotations

import uuid

import streamlit as st
from boot import memory_manager, llm_client  # <-- your existing wiring
from src.mentor import Mentor

# ---------------------------------------------------------------------------
# Session initialisation
# ---------------------------------------------------------------------------
if "mentor" not in st.session_state:
    st.session_state.mentor = Mentor(memory_manager, llm_client, user_id="u42")
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id: str | None = None
if "history" not in st.session_state:
    st.session_state.history: list[tuple[str, str]] = []  # [(role, text), ...]

mentor: Mentor = st.session_state.mentor
user_id = mentor.user_id

# ---------------------------------------------------------------------------
# Sidebar conversation management
# ---------------------------------------------------------------------------
st.sidebar.title("Mentor")
st.sidebar.markdown(
    """
**Tips**
- The mentor *remembers* what you say.
- Ask follow-up questions; the answers shape its memory.
- Use `🗑️ Clear chat window` to start fresh (dev only).
"""
)

threads_info = memory_manager.list_threads(user_id)

# Build mapping title -> id (unique titles enforced by uuid fallback)
title_to_id = {t["title"]: t["id"] for t in threads_info}
titles = list(title_to_id.keys())

conv_selection = st.sidebar.selectbox(
    "💬 Conversations",
    options=["➕   New Conversation"] + titles,
    index=0 if st.session_state.current_thread_id is None else titles.index(
        next((t for t, i in title_to_id.items() if i == st.session_state.current_thread_id), titles[0])
    )
    + 1,
    key="thread_selectbox",
)

if conv_selection.startswith("➕"):
    # Start fresh – pre-generate a thread-id so Mentor can use it right away
    st.session_state.current_thread_id = str(uuid.uuid4())
    st.session_state.history = []
else:
    st.session_state.current_thread_id = title_to_id[conv_selection]
    # Load history if we haven't yet or if switching threads
    thread_msgs = memory_manager.get_thread(st.session_state.current_thread_id) or []
    st.session_state.history = [(m["role"], m["content"]) for m in thread_msgs]

# Rename conversation option
with st.sidebar.expander("✏️ Rename conversation", expanded=False):
    new_title = st.text_input("New title", value="")
    if st.button("Rename") and new_title.strip() and st.session_state.current_thread_id:
        success = memory_manager.rename_thread(
            st.session_state.current_thread_id, user_id, new_title
        )
        if success:
            st.success("Title updated!")
            st.rerun()
        else:
            st.error("Could not rename thread.")

# Hard reset (dev only)
if st.sidebar.button("🗑️ Clear chat window"):
    st.session_state.history = []
    if conv_selection.startswith("➕"):
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

    # Persist history for display without reload

    # Reflect the new message list into sidebar list (titles might have been auto-generated)
    st.rerun()
