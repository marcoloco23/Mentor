"""
Streamlit chat wrapper for Ted
Run with:  streamlit run app.py
"""

from __future__ import annotations

import uuid

import streamlit as st
from src.boot import memory_manager, llm_client
from src.config import DEFAULT_USER_ID
from src.ted import Ted

# ---------------------------------------------------------------------------
# Session initialisation
# ---------------------------------------------------------------------------
if "ted" not in st.session_state:
    st.session_state.ted = Ted(memory_manager, llm_client, user_id=DEFAULT_USER_ID)
if "history" not in st.session_state:
    st.session_state.history: list[tuple[str, str]] = []  # [(role, text), ...]

ted: Ted = st.session_state.ted
user_id = ted.user_id

# ---------------------------------------------------------------------------
# Sidebar conversation management
# ---------------------------------------------------------------------------
st.sidebar.title("Ted")
st.sidebar.markdown(
    """
**Tips**
- Ted *remembers* what you say.
- Ask follow-up questions; the answers shape his memory.
- Use `��️ Clear chat window` to start fresh (dev only).
"""
)

# Hard reset (dev only)
if st.sidebar.button("🗑️ Clear chat window"):
    st.session_state.clear_chat = True
    st.rerun()

# ---------- 3. main chat ----------
st.title("🧸 Ted")

if getattr(st.session_state, "clear_chat", False):
    st.session_state.history = []
    st.session_state.clear_chat = False
else:
    recent_msgs = memory_manager.fetch_recent(user_id)
    st.session_state.history = [(m["role"], m["content"]) for m in recent_msgs]

for role, text in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)

if prompt := st.chat_input("Tell Ted something…"):
    # show user msg immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.history.append(("user", prompt))

    # get Ted reply
    with st.chat_message("assistant"):
        response = st.write_stream(ted.stream_reply(prompt))
    st.session_state.history.append(("assistant", response))

    # Persist history for display without reload

    # Reflect the new message list into sidebar list (titles might have been auto-generated)
    st.rerun()
