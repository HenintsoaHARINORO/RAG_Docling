# ui/chat.py
import time

import streamlit as st

from htmlTemplates import bot_template, user_template


def handle_question(question: str) -> None:
    chain = st.session_state.conversation

    # Render existing history first
    _render_chat_history()

    # User message
    st.write(user_template.replace("{{MSG}}", question), unsafe_allow_html=True)

    # Stream assistant response
    placeholder = st.empty()
    full_response = ""
    t0 = time.perf_counter()

    for chunk in chain.stream({"question": question}):
        full_response += chunk
        placeholder.write(
            bot_template.replace("{{MSG}}", full_response + "▌"),
            unsafe_allow_html=True,
        )

    elapsed = time.perf_counter() - t0
    placeholder.write(
        bot_template.replace("{{MSG}}", full_response),
        unsafe_allow_html=True,
    )
    st.caption(f"⏱ {elapsed:.2f}s")

    # Persist to session history
    st.session_state.chat_history.append({"role": "user", "content": question})
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

def _render_chat_history() -> None:
    if not st.session_state.get("chat_history"):
        return
    for msg in st.session_state.chat_history:
        template = user_template if msg["role"] == "user" else bot_template
        st.write(template.replace("{{MSG}}", msg["content"]), unsafe_allow_html=True)

