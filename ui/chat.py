# ui/chat.py
import time

import streamlit as st

from htmlTemplates import bot_template, user_template


def _inject_scroll_js(target: str = "bottom") -> None:
    """Inject JS to scroll to a specific element or position."""
    if target == "top":
        # Focuses the chat input bar and scrolls it into view
        js = """
        <script>
            (function() {
                const main = window.parent.document.querySelector('section.main');

                // Scroll to bottom where the input bar lives
                main.scrollTo({ top: main.scrollHeight, behavior: 'smooth' });

                // Also try to focus the textarea (chat_input widget)
                setTimeout(function() {
                    const input = window.parent.document.querySelector(
                        'textarea[data-testid="stChatInputTextArea"], input[aria-label="Ask a question"]'
                    );
                    if (input) {
                        input.focus();
                        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 300);
            })();
        </script>
        """
    elif target == "answer":
        # Scroll to the latest bot message
        js = """
        <script>
            (function() {
                const main = window.parent.document.querySelector('section.main');
                // Find all bot message containers and scroll to the last one
                const allElements = window.parent.document.querySelectorAll('[data-testid="stHtml"]');
                const last = allElements[allElements.length - 1];
                if (last) {
                    last.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    main.scrollTo({ top: main.scrollHeight, behavior: 'smooth' });
                }
            })();
        </script>
        """
    else:  # "bottom"
        js = """
        <script>
            (function() {
                const main = window.parent.document.querySelector('section.main');
                main.scrollTo({ top: main.scrollHeight, behavior: 'smooth' });
            })();
        </script>
        """
    st.components.v1.html(js, height=0, scrolling=False)


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

    # Scroll to the answer once it's fully rendered
    _inject_scroll_js("answer")

    # Persist to session history
    st.session_state.chat_history.append({"role": "user", "content": question})
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})




def _new_question_callback() -> None:
    """
    Clears the last question/answer pair from history so the user
    starts fresh, and sets a flag to scroll down to the input bar.
    """
    # Remove last Q&A pair from history so the chat resets visually
    if len(st.session_state.get("chat_history", [])) >= 2:
        st.session_state.chat_history = st.session_state.chat_history[:-2]

    st.session_state["_scroll_to_input"] = True


def _render_chat_history() -> None:
    if not st.session_state.get("chat_history"):
        return
    for msg in st.session_state.chat_history:
        template = user_template if msg["role"] == "user" else bot_template
        st.write(template.replace("{{MSG}}", msg["content"]), unsafe_allow_html=True)


def maybe_scroll_to_input() -> None:
    """
    Call this at the TOP of your main app page, before rendering anything else.
    Scrolls to and focuses the question input bar when the flag is set.
    """
    if st.session_state.pop("_scroll_to_input", False):
        _inject_scroll_js("top")