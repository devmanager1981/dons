"""Upload page for infrastructure file upload."""

import streamlit as st
from components.agent_activity import log_activity
from components.sidebar import navigate_to


def render_upload(client):
    """Render the infrastructure file upload page."""
    st.markdown(
        '<div style="background:#1a1a2e;padding:1rem 1.5rem;border-radius:10px;border-left:4px solid #0080FF;margin-bottom:1rem;">'
        '<p style="font-size:1.5rem;margin:0;color:#fff;">🏗️ Migration Architect</p>'
        '<p style="font-size:0.9rem;color:#aaa;margin:0.3rem 0 0 0;">Parses your AWS Terraform files and identifies resources for migration</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.header("📁 Upload Infrastructure Files")

    # If already uploaded, show status and next step
    if st.session_state.get("upload_id"):
        st.success(f"✅ File uploaded (ID: {st.session_state.upload_id})")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Upload a different file"):
                st.session_state.upload_id = None
                st.session_state.analysis_result = None
                st.session_state.escape_plan = None
                st.session_state.cost_result = None
                st.session_state.plan_id = None
                st.session_state.terraform_code = None
                st.rerun()
        with col2:
            if st.button("Next → Migration Summary", type="primary"):
                navigate_to("migration", "📊 Migration Summary")
                st.rerun()
        return

    accepted_types = ["tf", "json", "tfstate", "yaml", "zip"]
    st.info("Accepted file types: .tf, .tf.json, .tfstate, .yaml, .json, .zip")

    uploaded_file = st.file_uploader(
        "Choose an infrastructure file",
        type=accepted_types,
        key="infra_file_uploader",
    )

    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb < 0.01:
            file_size_kb = uploaded_file.size / 1024
            st.markdown(f"**File:** {uploaded_file.name}  \n**Size:** {file_size_kb:.1f} KB")
        else:
            st.markdown(f"**File:** {uploaded_file.name}  \n**Size:** {file_size_mb:.2f} MB")

        if file_size_mb > 50:
            st.warning("⚠️ File exceeds 50 MB. Upload may be slow or fail.")

        if st.button("Upload", type="primary"):
            with st.spinner("Uploading file..."):
                success, data = client.upload_infrastructure(uploaded_file)

            if success:
                upload_id = data.get("upload_id", "")
                st.session_state.upload_id = upload_id
                log_activity("migration_architect", "File uploaded", uploaded_file.name)
                st.success(f"✅ File uploaded successfully!")
                st.rerun()
            else:
                st.error(f"❌ Upload failed: {data}")
