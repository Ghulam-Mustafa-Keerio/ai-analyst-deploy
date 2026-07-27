from __future__ import annotations

import time
import streamlit as st

def render_auth() -> None:
    # Use custom CSS to animate the login container and hide the sidebar 
    # (since Streamlit doesn't natively let us conditionally render the sidebar wrapper easily before it executes)
    st.markdown(
        """
        <style>
        /* Hide sidebar entirely on auth page */
        section[data-testid="stSidebar"] { display: none; }
        
        /* Center the auth card */
        .auth-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 70vh;
        }
        
        /* Auth card animation and styling */
        .auth-card {
            background: var(--panel-strong);
            border: 1px solid var(--line);
            border-radius: var(--radius-lg);
            padding: 40px;
            box-shadow: var(--shadow-lg);
            width: 100%;
            max-width: 420px;
            animation: floatUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
            transform: translateY(20px);
            backdrop-filter: blur(16px);
        }
        
        @keyframes floatUp {
            to { opacity: 1; transform: translateY(0); }
        }
        
        .auth-title {
            text-align: center;
            font-weight: 800;
            font-size: 1.8rem;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .auth-subtitle {
            text-align: center;
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 32px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="auth-wrapper"><div class="auth-card">', unsafe_allow_html=True)
    
    st.markdown('<div class="auth-title">Agent OS</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">Autonomous Data Science Platform</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])
    
    with tab1:
        email = st.text_input("Email address", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Sign In", use_container_width=True, type="primary"):
            if email and password:
                with st.spinner("Authenticating..."):
                    time.sleep(0.8) # Simulate network request
                    st.session_state.authenticated = True
                    st.session_state.username = email.split('@')[0].capitalize()
                    st.rerun()
            else:
                st.error("Please enter both email and password.")
                
    with tab2:
        new_name = st.text_input("Full Name", key="reg_name")
        new_email = st.text_input("Email address", key="reg_email")
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        
        if st.button("Create Account", use_container_width=True, type="primary"):
            if new_name and new_email and new_pass:
                with st.spinner("Provisioning workspace..."):
                    time.sleep(1.2) # Simulate network request
                    st.session_state.authenticated = True
                    st.session_state.username = new_name.split()[0].capitalize()
                    st.rerun()
            else:
                st.error("Please fill out all fields to register.")

    st.markdown('</div></div>', unsafe_allow_html=True)
