import streamlit as st

def render_login_form() -> None:
    st.markdown("<style> .login-container { background: var(--bg-secondary); border-radius: 8px; padding: 1.5rem; max-width: 400px; margin: 2rem auto; } .login-input { background: #2f4f7b; color: white; border: none; padding: 0.8rem; margin: 1rem 0; width: 100%; } .login-button { background: #2563eb; color: white; padding: 0.8rem; border: none; width: 100%; font-size: 1rem; } .forgot-password { color: #94a3b8; margin-top: 1rem; text-align: right; } </style>", unsafe_allow_html=True)
    with st.container():
        st.markdown(
            """
            <div class='login-container'>
              <h2>Sign In</h2>
              <form>
                <div class='input-group'>
                  <label for='username'>Username</label>
                  <input type='text' id='username' class='login-input'>
                </div>
                <div class='input-group'>
                  <label for='password'>Password</label>
                  <input type='password' id='password' class='login-input'>
                </div>
                <button class='login-button'>Login</button>
                <a href='#' class='forgot-password'>Forgot password?</a>
              </form>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_signup_form():
    st.markdown("<style> .signup-container { background: var(--bg-secondary); border-radius: 8px; padding: 1.5rem; max-width: 450px; margin: 2rem auto; } .signup-input { background: #2f4f7b; color: white; border: none; padding: 0.8rem; margin: 1rem 0; width: 100%; } .signup-button { background: #2563eb; color: white; padding: 0.8rem; border: none; width: 100%; font-size: 1rem; } </style>", unsafe_allow_html=True)
    with st.container():
        st.markdown(
            """
            <div class='signup-container'>
              <h2>Create Account</h2>
              <form>
                <div class='input-group'>
                  <label for='email'>Email</label>
                  <input type='email' id='email' class='signup-input'>
                </div>
                <div class='input-group'>
                  <label for='username'>Username</label>
                  <input type='text' id='username' class='signup-input'>
                </div>
                <div class='input-group'>
                  <label for='password'>Password</label>
                  <input type='password' id='password' class='signup-input'>
                </div>
                <div class='input-group'>
                  <label for='confirm-password'>Confirm Password</label>
                  <input type='password' id='confirm-password' class='signup-input'>
                </div>
                <button class='signup-button'>Sign Up</button>
              </form>
            </div>
            """,
            unsafe_allow_html=True,
        )

if __name__ == '__main__':
    # Example implementation
    render_login_form()
    render_signup_form()