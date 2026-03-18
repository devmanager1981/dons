"""Landing page for DigitalOcean Native Stack."""

import streamlit as st


def render_home():
    """Render the landing/home page with platform overview."""
    st.markdown(
        '<h1 style="text-align:center;">☁️ DigitalOcean Native Stack</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align:center;font-size:1.2rem;color:#aaa;">'
        'AI-Powered Cloud Migration &amp; Store Intelligence for SMBs'
        '</p>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Two main features
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔧 Migration Assistance")
        st.markdown("""
        Upload your AWS Terraform files and get:
        - Instant infrastructure analysis
        - Cost comparison (typically 30-50% savings)
        - Auto-generated DigitalOcean Terraform
        - One-click deployment
        """)
        if st.button("Start Migration →", key="start_migration", type="primary"):
            st.session_state.current_section = "migration"
            st.session_state.current_page = "📁 Upload"
            st.rerun()

    with col2:
        st.markdown("### 🧠 Store Intelligence")
        st.markdown("""
        Powered by DigitalOcean Knowledge Base (OpenSearch):
        - Pre-built Knowledge Base with product docs
        - RAG-powered product Q&A via Gradient AI
        - Source citations for every answer
        - Semantic + lexical hybrid search
        """)
        if st.button("Start Intelligence →", key="start_intelligence", type="primary"):
            st.session_state.current_section = "intelligence"
            st.session_state.current_page = "💬 Ask Your Products"
            st.rerun()

    st.markdown("---")

    # AI Agents section — grouped by feature, bigger font, better colors
    st.markdown(
        '<h2 style="text-align:center;">🤖 Meet Your AI Agents</h2>',
        unsafe_allow_html=True,
    )

    # Migration agents
    st.markdown(
        '<h3 style="color:#0080FF;">🔧 Migration Agents</h3>',
        unsafe_allow_html=True,
    )
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            '<div style="background:#1a1a2e;padding:1.2rem;border-radius:10px;border-left:4px solid #0080FF;">'
            '<p style="font-size:1.4rem;margin:0;color:#fff;">🏗️ Migration Architect</p>'
            '<p style="font-size:0.95rem;color:#ccc;margin-top:0.5rem;">'
            'Analyzes AWS infrastructure, generates migration plans with risk analysis and rollback procedures'
            '</p></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            '<div style="background:#1a1a2e;padding:1.2rem;border-radius:10px;border-left:4px solid #0080FF;">'
            '<p style="font-size:1.4rem;margin:0;color:#fff;">⚙️ DevOps Agent</p>'
            '<p style="font-size:0.95rem;color:#ccc;margin-top:0.5rem;">'
            'Generates Terraform code, deploys infrastructure, monitors resources with self-healing'
            '</p></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            '<div style="background:#1a1a2e;padding:1.2rem;border-radius:10px;border-left:4px solid #0080FF;">'
            '<p style="font-size:1.4rem;margin:0;color:#fff;">🤖 AI Enablement</p>'
            '<p style="font-size:0.95rem;color:#ccc;margin-top:0.5rem;">'
            'Recommends AI/ML capabilities on DigitalOcean — Gradient AI, GPU Droplets, managed inference'
            '</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Store Intelligence agent
    st.markdown(
        '<h3 style="color:#00C853;">🧠 Store Intelligence Agent</h3>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="background:#1a1a2e;padding:1.2rem;border-radius:10px;border-left:4px solid #00C853;max-width:50%;">'
        '<p style="font-size:1.4rem;margin:0;color:#fff;">🧠 Store Intelligence</p>'
        '<p style="font-size:0.95rem;color:#ccc;margin-top:0.5rem;">'
        'RAG-powered Q&amp;A agent — uses DigitalOcean Knowledge Base (OpenSearch) for semantic search, answers via Gradient AI'
        '</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption("Powered by DigitalOcean Gradient AI (llama3-8b-instruct) · Built for the DO Hackathon 2026")
