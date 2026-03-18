"""Sidebar navigation for sub-pages within each section."""

import streamlit as st


def init_session_state():
    """Initialize all session state keys if not present."""
    defaults = {
        "current_section": "home",
        "current_page": "🏠 Home",
        "upload_id": None,
        "plan_id": None,
        "analysis_result": None,
        "escape_plan": None,
        "cost_result": None,
        "terraform_code": None,
        "terraform_validation": None,
        "terraform_errors": None,
        "deployment_status": None,
        "deployed_resources": None,
        "documents": [],
        "knowledge_base_status": None,
        "chat_history": [],
        "agent_activities": [],
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def clear_session_state():
    """Clear all session state and return to home."""
    for key in [
        "current_section", "current_page", "upload_id", "plan_id",
        "analysis_result", "escape_plan", "cost_result", "terraform_code",
        "terraform_validation", "terraform_errors",
        "deployment_status", "deployed_resources", "documents",
        "knowledge_base_status", "chat_history", "agent_activities",
    ]:
        if key in st.session_state:
            del st.session_state[key]
    init_session_state()


def navigate_to(section: str, page: str):
    """Navigate to a specific page."""
    st.session_state.current_section = section
    st.session_state.current_page = page


def render_sidebar(client) -> str:
    """Render sidebar with sub-navigation for the active section."""
    init_session_state()

    with st.sidebar:
        section = st.session_state.current_section

        if section == "migration":
            st.markdown("### 🔧 Migration Steps")
            migration_pages = [
                "📁 Upload",
                "📊 Migration Summary",
                "🚀 Infrastructure Deployment",
            ]
            for page in migration_pages:
                is_active = st.session_state.current_page == page
                label = f"▸ {page}" if is_active else page
                if st.button(label, key=f"mig_{page}", use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()

        elif section == "intelligence":
            st.markdown("### 🧠 Store Intelligence")
            intelligence_pages = [
                "💬 Ask Your Products",
            ]
            for page in intelligence_pages:
                is_active = st.session_state.current_page == page
                label = f"▸ {page}" if is_active else page
                if st.button(label, key=f"int_{page}", use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()

        else:
            # Home section
            st.markdown("### ☁️ DigitalOcean Native Stack")
            if st.button("🏠 Home", key="sidebar_home", use_container_width=True):
                st.session_state.current_section = "home"
                st.session_state.current_page = "🏠 Home"
                st.rerun()
            st.caption("Or select Migration / Intelligence from the top bar.")

    return st.session_state.current_page
