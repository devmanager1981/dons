"""Main entry point for the Streamlit app."""

import streamlit as st
from api_client import DONSApiClient
from config import BACKEND_URL
from components.sidebar import render_sidebar, init_session_state
from components.agent_activity import render_agent_activity_top
from views.home import render_home
from views.migration.upload import render_upload
from views.migration.summary import render_summary
from views.migration.deployment import render_deployment
from views.intelligence.chat import render_chat

st.set_page_config(
    page_title="DigitalOcean Native Stack",
    layout="wide",
    page_icon="☁️",
)

# Initialize session state and API client
init_session_state()
client = DONSApiClient(base_url=BACKEND_URL)

# Check backend health
success, _ = client.health_check()

# --- Top bar: horizontal nav + connection status + agent activity ---
top_cols = st.columns([1, 1, 1, 1, 1, 2])
with top_cols[0]:
    if st.button("🏠 Home", key="top_home", use_container_width=True):
        st.session_state.current_section = "home"
        st.session_state.current_page = "🏠 Home"
        st.rerun()
with top_cols[1]:
    if st.button("🔧 Migration", key="top_migration", use_container_width=True):
        st.session_state.current_section = "migration"
        st.session_state.current_page = "📁 Upload"
        st.rerun()
with top_cols[2]:
    if st.button("🧠 Intelligence", key="top_intelligence", use_container_width=True):
        st.session_state.current_section = "intelligence"
        st.session_state.current_page = "💬 Ask Your Products"
        st.rerun()
with top_cols[3]:
    if success:
        st.markdown("🟢 Connected to DigitalOcean")
    else:
        st.markdown("🔴 Disconnected")
with top_cols[4]:
    if st.button("🔄 Start Over", key="top_reset", use_container_width=True):
        from components.sidebar import clear_session_state
        clear_session_state()
        st.rerun()
with top_cols[5]:
    render_agent_activity_top()

# Warning banner when disconnected
if not success:
    st.warning(
        "⚠️ Unable to connect to backend. "
        "Please ensure the API server is running at " + BACKEND_URL
    )

# Render sidebar (sub-navigation within sections)
selected_page = render_sidebar(client)

# Page routing
if selected_page == "🏠 Home":
    render_home()
elif selected_page == "📁 Upload":
    render_upload(client)
elif selected_page == "📊 Migration Summary":
    render_summary(client)
elif selected_page == "🚀 Infrastructure Deployment":
    render_deployment(client)
elif selected_page == "💬 Ask Your Products":
    render_chat(client)
