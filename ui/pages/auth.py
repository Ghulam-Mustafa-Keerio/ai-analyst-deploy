from __future__ import annotations

import time
import streamlit as st


def render_auth() -> None:
    # Force high-contrast colors and override Streamlit theme defaults
    st.markdown(
        """
        <style>
        /* 1. Global Reset for Streamlit Theme Variables */
        :root {
            --text-color: #ffffff !important;
            --primary-color: #2563eb !important;
        }

        /* Hide Sidebar & Header Header */
        section[data-testid="stSidebar"] { display: none; }
        header[data-testid="stHeader"] { background: transparent; }
        
        /* Full Page Dark Background */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #020617 0%, #0f172a 100%) !important;
            min-height: 100vh;
            position: relative;
            overflow: hidden;
        }

        /* Card Container */
        [data-testid="stMainBlockContainer"] {
            max-width: 480px !important;
            margin: auto !important;
            padding: 2.5rem 2rem !important;
            border-radius: 24px;
            background: rgba(15, 23, 42, 0.92) !important;
            border: 1px solid rgba(148, 163, 184, 0.25) !important;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 35px rgba(59, 130, 246, 0.2) !important;
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            animation: cardFadeIn 800ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        @keyframes cardFadeIn {
            0% { opacity: 0; transform: translateY(20px) scale(0.97); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }

        @keyframes badgePulse {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-3px); }
        }

        /* 2. Header & Subtitle Contrast Overrides */
        .auth-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 9999px;
            background: rgba(37, 99, 235, 0.25) !important;
            border: 1px solid rgba(147, 197, 253, 0.5) !important;
            color: #bfdbfe !important; /* Bright Blue */
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.85rem;
            animation: badgePulse 3s ease-in-out infinite;
        }

        .auth-title {
            font-size: 2.25rem;
            font-weight: 800;
            line-height: 1.1;
            color: #ffffff !important;
            background: linear-gradient(135deg, #ffffff 0%, #60a5fa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.35rem;
        }

        .auth-subtitle {
            color: #cbd5e1 !important; /* Crisp Light Grey */
            font-size: 0.95rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }

        /* 3. Input Label and Field Colors */
        [data-testid="stTextInput"] label,
        [data-testid="stTextInput"] label p {
            color: #f8fafc !important; /* Pure Bright White */
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }

        [data-testid="stTextInput"] input {
            background-color: #1e293b !important; /* Solid Dark Slate */
            color: #ffffff !important;
            border: 1px solid #475569 !important;
            border-radius: 10px !important;
            transition: all 0.25s ease-in-out !important;
        }

        [data-testid="stTextInput"] input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.35) !important;
            transform: translateY(-1px);
        }

        /* Eye Icon inside password input */
        [data-testid="stTextInput"] button {
            color: #94a3b8 !important;
            background: transparent !important;
        }

        /* 4. Tab Navigation High-Contrast Styling */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #1e293b !important;
            padding: 4px;
            border-radius: 12px;
            border: 1px solid #334155 !important;
        }

        [data-testid="stTabs"] [data-baseweb="tab"] {
            height: 40px;
            border-radius: 8px;
            border: none !important;
            padding: 0 16px;
            transition: all 0.2s ease;
        }

        /* Inactive Tab Text */
        [data-testid="stTabs"] [data-baseweb="tab"] p,
        [data-testid="stTabs"] [data-baseweb="tab"] span {
            color: #94a3b8 !important;
            font-weight: 600 !important;
        }

        /* Active Tab Styling */
        [data-testid="stTabs"] [aria-selected="true"] {
            background-color: #2563eb !important;
        }

        [data-testid="stTabs"] [aria-selected="true"] p,
        [data-testid="stTabs"] [aria-selected="true"] span {
            color: #ffffff !important; /* Solid White */
            font-weight: 700 !important;
        }

        /* 5. Primary Sign In / Create Account Buttons */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
            transition: all 0.2s ease-in-out !important;
        }

        div.stButton > button[kind="primary"] p,
        div.stButton > button[kind="primary"] span {
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
        }

        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.5) !important;
        }

        /* 6. Social Provider Buttons & Divider */
        .auth-divider {
            display: flex;
            align-items: center;
            text-align: center;
            color: #94a3b8 !important;
            font-size: 0.8rem;
            font-weight: 600;
            margin: 1.5rem 0 1.25rem;
        }

        .auth-divider::before,
        .auth-divider::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid #334155;
        }

        .auth-divider span {
            padding: 0 0.75rem;
        }

        .social-btn-container {
            display: flex;
            gap: 10px;
            justify-content: center;
        }

        .social-btn {
            flex: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 0.65rem 1rem;
            border-radius: 10px;
            background: #1e293b !important;
            border: 1px solid #334155 !important;
            color: #f8fafc !important;
            font-size: 0.875rem;
            font-weight: 600;
            text-decoration: none !important;
            transition: all 0.2s ease-in-out;
        }

        .social-btn:hover {
            background: #334155 !important;
            border-color: #60a5fa !important;
            color: #ffffff !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }

        /* Responsive Breakpoints */
        @media (max-width: 640px) {
            [data-testid="stMainBlockContainer"] {
                margin: 1rem !important;
                padding: 1.5rem 1.25rem !important;
            }
            .auth-title { font-size: 1.75rem; }
            .social-btn-container { flex-direction: column; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header Branding
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div class="auth-badge">Secure Workspace Access</div>
            <div class="auth-title">Agent OS</div>
            <div class="auth-subtitle">Autonomous Data Science Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Authentication Tabs
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])

    with tab1:
        email = st.text_input("Email address", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Sign In", use_container_width=True, type="primary"):
            if email and password:
                with st.spinner("Authenticating..."):
                    time.sleep(0.8)
                    st.session_state.authenticated = True
                    st.session_state.username = email.split("@")[0].capitalize()
                    st.rerun()
            else:
                st.error("Please enter both email and password.")

        st.markdown(
            """
            <div style="text-align: center; margin-top: 1rem;">
                <a href="#" style="color: #AAAAAA; text-decoration: none; font-size: 0.875rem; font-weight: 500;">Forgot password?</a>
            </div>
            
            <div class="auth-divider">
                <span>OR CONTINUE WITH</span>
            </div>

            <div class="social-btn-container">
                <a href="#" class="social-btn">
                    <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"/><path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"/><path fill="#FBBC05" d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 10.8 0 12s.7 2.3 1.9 4.7l3.7-2.9z"/><path fill="#34A853" d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 16C3.7 19.7 7.5 23 12 23z"/></svg>
                    Google
                </a>
                <a href="#" class="social-btn">
                    <svg width="18" height="18" viewBox="0 0 23 23"><path fill="#f35325" d="M1 1h10v10H1z"/><path fill="#81bc06" d="M12 1h10v10H12z"/><path fill="#05a6f0" d="M1 12h10v10H1z"/><path fill="#ffba08" d="M12 12h10v10H12z"/></svg>
                    Microsoft
                </a>
                <a href="#" class="social-btn">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                    GitHub
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab2:
        new_name = st.text_input("Full Name", key="reg_name")
        new_email = st.text_input("Email address", key="reg_email")
        new_pass = st.text_input("Password", type="password", key="reg_pass")

        if st.button("Create Account", use_container_width=True, type="primary"):
            if new_name and new_email and new_pass:
                with st.spinner("Provisioning workspace..."):
                    time.sleep(1.2)
                    st.session_state.authenticated = True
                    st.session_state.username = new_name.split()[0].capitalize()
                    st.rerun()
            else:
                st.error("Please fill out all fields to register.")