"""Infrastructure deployment page for Terraform generation and deployment."""

import streamlit as st
from components.agent_activity import log_activity
from components.sidebar import navigate_to


def render_deployment(client):
    """Render the infrastructure deployment page."""
    st.markdown(
        '<div style="background:#1a1a2e;padding:1rem 1.5rem;border-radius:10px;border-left:4px solid #0080FF;margin-bottom:1rem;">'
        '<p style="font-size:1.5rem;margin:0;color:#fff;">⚙️ DevOps Agent</p>'
        '<p style="font-size:0.9rem;color:#aaa;margin:0.3rem 0 0 0;">Generates Terraform code, validates syntax, and deploys to DigitalOcean</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.header("🚀 Infrastructure Deployment")

    plan_id = st.session_state.get("plan_id")
    if not plan_id:
        st.warning("⚠️ Please complete the Migration Summary step first.")
        if st.button("← Go to Migration Summary"):
            navigate_to("migration", "📊 Migration Summary")
            st.rerun()
        return

    # Fetch terraform code if not cached
    if not st.session_state.get("terraform_code"):
        with st.spinner("Generating Terraform code..."):
            success, data = client.generate_terraform(plan_id)
            if success:
                st.session_state.terraform_code = data.get("terraform_code", "")
                st.session_state.terraform_validation = data.get("validation_status", "unknown")
                st.session_state.terraform_errors = data.get("validation_errors", [])
                log_activity("devops", "Generated Terraform code", f"{data.get('resource_count', 0)} resources")
            else:
                st.error(f"Failed to generate Terraform: {data}")
                return

    terraform_code = st.session_state.get("terraform_code", "")
    validation_status = st.session_state.get("terraform_validation", "unknown")
    validation_errors = st.session_state.get("terraform_errors", [])

    if validation_status == "valid":
        st.success("✅ Terraform code is valid")
    elif validation_status == "invalid":
        st.error("❌ Terraform validation failed")
        for err in validation_errors:
            st.error(err)

    st.subheader("Generated Terraform Code")
    st.code(terraform_code, language="hcl")

    st.download_button(
        label="📥 Download Terraform (.tf)",
        data=terraform_code,
        file_name="main.tf",
        mime="text/plain",
    )

    st.markdown("---")

    # Deploy to DigitalOcean
    st.subheader("Deploy to DigitalOcean")

    deployment_status = st.session_state.get("deployment_status")

    if deployment_status == "completed":
        st.success("✅ Infrastructure deployed successfully!")
        deployed = st.session_state.get("deployed_resources", [])
        if deployed:
            with st.expander("📋 Deployed Resources", expanded=True):
                for r in deployed:
                    st.markdown(f"- **{r.get('name', 'N/A')}** ({r.get('type', 'N/A')}) — ID: `{r.get('id', 'N/A')}` — Status: {r.get('status', 'N/A')}")
        st.balloons()

        # Destroy option
        if st.button("🗑️ Destroy Infrastructure", type="secondary"):
            with st.spinner("Destroying infrastructure..."):
                success, data = client.destroy(plan_id)
            if success:
                st.session_state.deployment_status = None
                st.session_state.deployed_resources = None
                log_activity("devops", "Infrastructure destroyed")
                st.success("Infrastructure destroyed.")
                st.rerun()
            else:
                st.error(f"Destroy failed: {data}")

    elif deployment_status == "partial":
        st.warning("⚠️ Deployment partially completed — some resources may still be provisioning.")
        deployed = st.session_state.get("deployed_resources", [])
        if deployed:
            with st.expander("📋 Deployed Resources", expanded=True):
                for r in deployed:
                    st.markdown(f"- **{r.get('name', 'N/A')}** ({r.get('type', 'N/A')}) — ID: `{r.get('id', 'N/A')}` — Status: {r.get('status', 'N/A')}")

        if st.button("🗑️ Destroy Infrastructure", type="secondary"):
            with st.spinner("Destroying infrastructure..."):
                success, data = client.destroy(plan_id)
            if success:
                st.session_state.deployment_status = None
                st.session_state.deployed_resources = None
                log_activity("devops", "Infrastructure destroyed")
                st.success("Infrastructure destroyed.")
                st.rerun()
            else:
                st.error(f"Destroy failed: {data}")

    elif deployment_status == "failed":
        st.error("❌ Deployment failed. Check logs and try again.")
        if st.button("🔄 Retry Deployment", type="primary"):
            st.session_state.deployment_status = None
            st.rerun()

    else:
        st.info("Click below to deploy the generated Terraform to DigitalOcean.")
        if st.button("🚀 Deploy to DigitalOcean", type="primary"):
            with st.spinner("Deploying infrastructure to DigitalOcean..."):
                success, data = client.deploy(plan_id)

            if success:
                st.session_state.deployment_status = data.get("status", "completed")
                st.session_state.deployed_resources = data.get("deployed_resources", [])
                log_activity("devops", "Deployed infrastructure", f"{data.get('deployed_count', 0)} resources")
                st.rerun()
            else:
                st.session_state.deployment_status = "failed"
                log_activity("devops", "Deployment failed", str(data)[:60])
                st.error(f"Deployment failed: {data}")
                st.rerun()

    # Navigation
    st.markdown("---")
    if st.button("← Back to Migration Summary"):
        navigate_to("migration", "📊 Migration Summary")
        st.rerun()
