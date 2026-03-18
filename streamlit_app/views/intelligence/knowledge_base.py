"""Knowledge Base status page for Store Intelligence."""

import streamlit as st
from components.sidebar import navigate_to


def render_knowledge_base(client):
    """Render the knowledge base overview with DO KB status."""
    st.markdown(
        '<div style="background:#1a1a2e;padding:1rem 1.5rem;border-radius:10px;border-left:4px solid #00C853;margin-bottom:1rem;">'
        '<p style="font-size:1.5rem;margin:0;color:#fff;">🧠 Store Intelligence Agent</p>'
        '<p style="font-size:0.9rem;color:#aaa;margin:0.3rem 0 0 0;">Manages your indexed product knowledge base</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.header("📚 Knowledge Base")

    success, data = client.get_knowledge_base_status()

    if not success:
        st.error(f"Could not load knowledge base status: {data}")
        return

    total_docs = data.get("total_documents", 0)
    total_chunks = data.get("total_chunks", 0)
    index_health = data.get("index_health", "red")
    kb_status = data.get("kb_status", "not_created")
    kb_uuid = data.get("kb_uuid")
    spaces_bucket = data.get("spaces_bucket", "1donsspaces")
    spaces_region = data.get("spaces_region", "nyc3")
    embedding_model = data.get("embedding_model", "GTE Large v1.5")

    # --- KB Status Banner ---
    _render_kb_status_banner(kb_status, kb_uuid)

    # --- Metrics ---
    health_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(index_health, "🔴")
    col1, col2, col3 = st.columns(3)
    col1.metric("Documents", total_docs)
    col2.metric("Chunks", total_chunks)
    col3.metric("KB Health", f"{health_icon} {index_health.title()}")

    st.markdown("---")

    # --- Infrastructure Info ---
    st.subheader("☁️ Infrastructure")
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.markdown(f"**Spaces Bucket:** `{spaces_bucket}` ({spaces_region})")
        st.markdown(f"**Upload Path:** `documents/`")
    with info_col2:
        st.markdown(f"**Embedding Model:** {embedding_model}")
        if kb_uuid:
            st.markdown(f"**KB ID:** `{kb_uuid[:12]}...`")
        else:
            st.markdown("**KB ID:** Not yet created")

    st.markdown("---")

    if total_docs == 0:
        st.info("No documents yet. Head to Document Upload to add product docs.")
        if st.button("← Go to Document Upload"):
            navigate_to("intelligence", "📤 Document Upload")
            st.rerun()
        return

    # --- Document List ---
    st.subheader("Indexed Documents")
    _list_documents(client)

    # Navigation
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Upload More Documents"):
            navigate_to("intelligence", "📤 Document Upload")
            st.rerun()
    with col2:
        if st.button("Ask Your Products →", type="primary"):
            navigate_to("intelligence", "💬 Ask Your Products")
            st.rerun()


def _render_kb_status_banner(kb_status, kb_uuid):
    """Show a status banner based on KB provisioning state."""
    if kb_status in ("active", "ready", "completed"):
        st.success("✅ Knowledge Base is active — semantic search is ready")
    elif kb_status in ("provisioning", "indexing", "processing"):
        st.warning(f"⏳ Knowledge Base is {kb_status}... Semantic search will be available once indexing completes. SQL fallback is active in the meantime.")
    elif kb_status == "not_created":
        if kb_uuid:
            st.info("🔄 Knowledge Base exists but status is unknown. SQL fallback search is active.")
        else:
            st.info("📦 Knowledge Base will be auto-created when you upload your first document. SQL fallback search is active until then.")
    else:
        st.warning(f"⚠️ Knowledge Base status: {kb_status}. SQL fallback search is active.")


def _list_documents(client):
    """List documents with delete buttons."""
    docs = st.session_state.get("documents", [])
    if not docs:
        st.caption("Upload documents to see them listed here.")
        return

    for doc in docs:
        col1, col2 = st.columns([4, 1])
        chunks = doc.get("chunk_count") or 0
        status_icon = {"completed": "✅", "processing": "⏳", "failed": "❌", "pending": "🔄"}.get(doc.get("status", ""), "❓")
        col1.markdown(f"{status_icon} **{doc['filename']}** — {chunks} chunks — {doc['status']}")
        if col2.button("🗑️", key=f"del_{doc['document_id']}"):
            ok, resp = client.delete_document(doc["document_id"])
            if ok:
                st.session_state.documents = [
                    d for d in st.session_state.documents
                    if d["document_id"] != doc["document_id"]
                ]
                st.rerun()
            else:
                st.error(f"Delete failed: {resp}")
