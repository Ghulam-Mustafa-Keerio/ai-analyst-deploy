from __future__ import annotations

import streamlit as st

def render_overview() -> None:
    st.markdown('<div class="eyebrow">Platform Guidelines</div>', unsafe_allow_html=True)
    
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <h1>Welcome, {st.session_state.username or 'Data Scientist'} 👋</h1>
            <span class="badge primary">Agent OS v2.0</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.caption("Learn how to navigate and operate the Autonomous Data Science pipeline.")
    st.markdown('<hr class="soft">', unsafe_allow_html=True)
    
    st.markdown(
        """
        ### 🚀 Getting Started
        The **Agent OS** is an autonomous platform that handles data profiling, machine learning model training, and insight generation. 
        Follow these three core steps to run a successful analysis:
        """
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="card" style="min-height: 220px;">
                <div style="font-size: 2rem; margin-bottom: 12px;">📂</div>
                <div style="font-weight: 700; margin-bottom: 8px;">1. Ingest Data</div>
                <div class="small-muted">Go to the <b>Dashboard</b> tab. Upload an Excel, JSON, CSV, or Parquet file. Alternatively, connect directly to a remote SQL database, Google Sheet, or REST API.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
            <div class="card" style="min-height: 220px;">
                <div style="font-size: 2rem; margin-bottom: 12px;">⚙️</div>
                <div style="font-weight: 700; margin-bottom: 8px;">2. Launch Agents</div>
                <div class="small-muted">Set the autonomy level (Manual, Assisted, or Autonomous) and select your target prediction column. Click <b>Start agent run</b> to spawn the intelligent agents.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            """
            <div class="card" style="min-height: 220px;">
                <div style="font-size: 2rem; margin-bottom: 12px;">🧠</div>
                <div style="font-weight: 700; margin-bottom: 8px;">3. Analyze & Query</div>
                <div class="small-muted">Watch the agents debate and train models live on the <b>Intelligence</b> tab. Once completed, query the trained model dynamically on the <b>Advisor</b> tab.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown('<br><hr class="soft">', unsafe_allow_html=True)
    
    st.markdown("### 🧭 Autonomy Levels Explained")
    st.markdown(
        """
        - **Manual**: You explicitly select the ML algorithm (e.g., Random Forest) and the precise input features to use. Best for strict control.
        - **Assisted**: You select the target. The agents profile the data and automatically select the optimal features for you, but rely on deterministic model selection.
        - **Autonomous (Recommended)**: The LLM layer takes over. Multiple agents debate the problem, determine the business domain, select features, and hyper-optimize the best model candidate entirely on their own.
        """
    )
    
    st.info("💡 **Pro Tip**: Use the 'Built-in sample' datasets on the Dashboard to run your first pipeline if you don't have data on hand.")
    
    if st.button("Logout", type="secondary"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()
