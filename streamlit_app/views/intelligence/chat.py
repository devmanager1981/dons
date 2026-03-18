"""Chat interface for Store Intelligence RAG Q&A."""

import streamlit as st
from components.agent_activity import log_activity


def render_chat(client):
    """Render the Ask Your Products chat interface."""
    st.markdown(
        '<div style="background:#1a1a2e;padding:1rem 1.5rem;border-radius:10px;border-left:4px solid #00C853;margin-bottom:1rem;">'
        '<p style="font-size:1.5rem;margin:0;color:#fff;">🧠 Store Intelligence Agent</p>'
        '<p style="font-size:0.9rem;color:#aaa;margin:0.3rem 0 0 0;">RAG-powered Q&amp;A — answers questions using your uploaded product documentation</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.header("💬 Ask Your Products")

    # Clear chat button
    col1, col2 = st.columns([4, 1])
    col1.caption("Ask questions about your products using the Knowledge Base.")
    if col2.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    # Welcome message if empty
    if not st.session_state.chat_history:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": (
                "Hi! I'm the Store Intelligence agent. "
                "Ask me anything about your products — I'll search the Knowledge Base for answers."
            ),
        })

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📎 Sources"):
                    for src in msg["sources"]:
                        st.markdown(
                            f"**{src['filename']}** "
                            f"(relevance {src['relevance_score']:.2f})"
                        )
                        st.caption(src["chunk_excerpt"])

    # Chat input
    if question := st.chat_input("Ask about your products..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Get answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                success, data = client.ask_intelligence(question)

            if success:
                answer = data.get("answer", "No answer returned.")
                sources = data.get("sources", [])
                model = data.get("model_used", "")

                st.markdown(answer)
                if model:
                    st.caption(f"Model: {model}")
                if sources:
                    with st.expander("📎 Sources"):
                        for src in sources:
                            st.markdown(
                                f"**{src['filename']}** "
                                f"(relevance {src['relevance_score']:.2f})"
                            )
                            st.caption(src["chunk_excerpt"])

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })
                log_activity("store_intelligence", "Answered question", question[:60])
            else:
                err = f"Sorry, something went wrong: {data}"
                st.error(err)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": err,
                })
