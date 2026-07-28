from __future__ import annotations

import time
import streamlit as st

def render_auth() -> None:
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] { display: none; }

        .auth-page {
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 24px 16px;
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.24), transparent 28%),
                radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.18), transparent 32%),
                linear-gradient(135deg, rgba(2, 6, 23, 0.98), rgba(15, 23, 42, 0.96));
        }

        .auth-card {
            position: relative;
            width: min(100%, 480px);
            padding: 32px 28px 28px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 24px;
            background: rgba(15, 23, 42, 0.86);
            box-shadow: 0 26px 70px rgba(2, 6, 23, 0.35);
            backdrop-filter: blur(18px);
            overflow: hidden;
            animation: authFadeIn 700ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
            transform: translateY(18px) scale(0.985);
        }

        .auth-card::before {
            content: "";
            position: absolute;
            inset: -1px;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.55), rgba(14, 165, 233, 0.18));
            z-index: -1;
            filter: blur(24px);
            opacity: 0.8;
            animation: authGlow 4s ease-in-out infinite;
        }

        .auth-card::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(120deg, rgba(255,255,255,0.08), transparent 35%, rgba(255,255,255,0.06));
            pointer-events: none;
            animation: authShine 5s linear infinite;
        }

        @keyframes authFadeIn {
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        @keyframes authGlow {
            0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
            50% { transform: translate3d(4px, -6px, 0) scale(1.03); }
        }

        @keyframes authShine {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .auth-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 12px;
            border-radius: 999px;
            background: rgba(37, 99, 235, 0.16);
            color: #bfdbfe;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 16px;
            animation: authPulse 2.8s ease-in-out infinite;
        }

        @keyframes authPulse {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-2px); }
        }

        .auth-title {
            text-align: left;
            font-weight: 800;
            font-size: 2rem;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #dbeafe, #60a5fa 55%, #93c5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .auth-subtitle {
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 24px;
            line-height: 1.6;
        }

        .auth-card .stTabs [data-testid="stBaseButton-secondary"] {
            transition: transform 180ms ease, background-color 180ms ease;
        }

        .auth-card .stTabs [data-testid="stBaseButton-secondary"]:hover {
            transform: translateY(-1px);
        }

        .auth-card .stTextInput input {
            transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
        }

        .auth-card .stTextInput input:focus {
            border-color: #60a5fa;
            box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
            transform: translateY(-1px);
        }

        .auth-card .stButton > button {
            transition: transform 180ms ease, box-shadow 180ms ease;
        }

        .auth-card .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.16);
        }

        @media (max-width: 640px) {
            .auth-card {
                padding: 24px 20px 20px;
                border-radius: 20px;
            }

            .auth-title {
                font-size: 1.7rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="auth-page"><div class="auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="auth-badge">Secure workspace access</div>', unsafe_allow_html=True)
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
