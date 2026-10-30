"""
Streamlit UI component for system diagnostics and provider status.
"""

import streamlit as st
import requests


def render_system_status(backend_url: str):
    """Fetch and display backend health, database status, and provider readiness."""
    try:
        resp = requests.get(f"{backend_url}/api/health", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            db_info = data.get("database", {})
            providers = data.get("providers", {})

            st.sidebar.success("🟢 Backend Connected", icon="✅")
            with st.sidebar.expander("⚙️ System Status", expanded=False):
                st.write(f"**Database:** {db_info.get('engine', 'Unknown')}")
                st.write(f"**pgvector:** {'✅ Active' if db_info.get('pgvector_enabled') else '⚠️ Fallback'}")
                st.write(f"**OpenAI:** {'✅ Configured' if providers.get('openai') else '❌ Not set'}")
                st.write(f"**Gemini:** {'✅ Configured' if providers.get('gemini') else '❌ Not set'}")
                st.write(f"**Tavily Search:** {'✅ Configured' if providers.get('tavily') else 'ℹ️ DuckDuckGo Fallback'}")
        else:
            st.sidebar.error("⚠️ Backend returned non-200 status")
    except Exception:
        st.sidebar.error("🔴 Backend Offline (Start with `uvicorn backend.main:app`)")

