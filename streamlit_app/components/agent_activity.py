"""Agent Activity Feed component."""

from datetime import datetime
import streamlit as st


AGENTS = {
    "migration_architect": {"name": "Migration Architect", "icon": "🏗️"},
    "devops": {"name": "DevOps Agent", "icon": "⚙️"},
    "ai_enablement": {"name": "AI Enablement", "icon": "🤖"},
    "store_intelligence": {"name": "Store Intelligence", "icon": "🧠"},
}


def log_activity(agent_key: str, action: str, detail: str = ""):
    """Log an agent activity to session state."""
    if "agent_activities" not in st.session_state:
        st.session_state.agent_activities = []

    agent = AGENTS.get(agent_key, {"name": agent_key, "icon": "🔹"})
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "agent": agent["name"],
        "icon": agent["icon"],
        "action": action,
        "detail": detail,
    }
    st.session_state.agent_activities.insert(0, entry)
    st.session_state.agent_activities = st.session_state.agent_activities[:50]


def render_agent_activity_top():
    """Render compact agent activity in the top bar."""
    activities = st.session_state.get("agent_activities", [])
    if not activities:
        st.caption("🤖 No agent activity yet")
        return

    latest = activities[0]
    st.markdown(
        f"{latest['icon']} **{latest['agent']}** — {latest['action']}",
    )
    if len(activities) > 1:
        with st.popover(f"📋 {len(activities)} activities"):
            for entry in activities[:10]:
                st.markdown(
                    f"{entry['icon']} **{entry['agent']}** "
                    f"<small>{entry['timestamp']} — {entry['action']}</small>",
                    unsafe_allow_html=True,
                )
