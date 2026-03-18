"""Document Upload page for Store Intelligence."""

import streamlit as st
from components.agent_activity import log_activity
from components.sidebar import navigate_to


def render_document_upload(client):
    """Render the document upload interface for Store Intelligence."""
    st.markdown(
        '<div style="background:#1a1a2e;padding:1rem 1.5rem;border-radius:10px;border-left:4px solid #00C853;margin-bottom:1rem;">'
        '<p style="font-size:1.5rem;margin:0;color:#fff;">🤖 AI Enablement Agent</p>'
        '<p style="font-size:0.9rem;color:#aaa;margin:0.3rem 0 0 0;">Extracts text, chunks documents, and generates embeddings for vector search</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.header("📤 Document Upload")
    st.caption("Upload product PDFs, manuals, or text files to build your knowledge base.")

    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "txt", "md", "csv"],
        accept_multiple_files=True,
        key="doc_uploader",
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected**")
        for f in uploaded_files:
            size_kb = len(f.getvalue()) / 1024
            st.text(f"  • {f.name}  ({size_kb:.1f} KB)")

        if st.button("⬆️ Upload & Process", type="primary"):
            with st.spinner("Uploading and processing documents..."):
                success, data = client.upload_documents(uploaded_files)

            if success:
                docs = data.get("documents", [])
                st.success(f"Uploaded {data.get('total_uploaded', len(docs))} document(s)")
                for doc in docs:
                    status_icon = "✅" if doc["status"] == "completed" else "⏳"
                    chunks = doc.get("chunk_count") or 0
                    st.markdown(
                        f"{status_icon} **{doc['filename']}** — "
                        f"{doc['status']}  ({chunks} chunks)"
                    )
                existing_ids = {d["document_id"] for d in st.session_state.documents}
                for doc in docs:
                    if doc["document_id"] not in existing_ids:
                        st.session_state.documents.append(doc)
                st.session_state.knowledge_base_status = None
                total_chunks = sum(d.get("chunk_count") or 0 for d in docs)
                log_activity("ai_enablement", "Indexed documents", f"{len(docs)} docs, {total_chunks} chunks")
                log_activity("store_intelligence", "Knowledge base updated")
            else:
                st.error(f"Upload failed: {data}")
    else:
        st.info("Drag and drop files above, or click Browse to select.")

    # Navigation to next steps
    if st.session_state.get("documents"):
        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("View Knowledge Base →"):
                navigate_to("intelligence", "📚 Knowledge Base")
                st.rerun()
        with col2:
            if st.button("Ask Your Products →", type="primary"):
                navigate_to("intelligence", "💬 Ask Your Products")
                st.rerun()
