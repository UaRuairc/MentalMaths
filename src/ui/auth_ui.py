import streamlit as st
from src.database.auth.service import SupabaseLogin
from src.state_management import ConfigManager
from src.ui.widgets import MakeWidget

ENABLE_GOOGLE_LOGIN = True
ENABLE_GITHUB_LOGIN = False
ENABLE_EMAIL_LOGIN = False

login_handler = SupabaseLogin()
def auth_ui():
    """Render the login component"""
    login_handler.restore_session()
    if st.session_state.get("user"):
        display_already_logged_in()
        return

    display_auth_login()

def display_auth_login():

    col1, col2, col3  = st.columns([1 ,1 ,1], vertical_alignment="center")
    google_logo = "https://www.gstatic.com/images/branding/product/1x/googleg_32dp.png"
    github_logo = "https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png"

    if ENABLE_GOOGLE_LOGIN:
        with col1:
            st.markdown(f"<span style='font-size:36px;'>{":material/key:"}</span>", unsafe_allow_html=True)
        with col2:
            if st.button(f"![Google]({google_logo})", key="google_login_btn"):
                login_handler.handle_google_login()

    if ENABLE_GITHUB_LOGIN:
        with col3:
            if st.button(f"![GitHub]({github_logo})", key="github_login_btn"):
                login_handler.handle_google_login()


    st.divider()

    if ENABLE_EMAIL_LOGIN:
        st.markdown("**Or login with email**")

        # Email/Password login
        ConfigManager.add_widget("login_email", "text_input_boxes",
                                 **{"label": "Email", "placeholder": "your@email.com"})
        MakeWidget(
            "login_email",
            "text_input_boxes",
        ).render()
        ConfigManager.add_widget("login_password", "text_input_boxes",
                                 **{"label": "Email", "placeholder": "password"})
        MakeWidget(
            "login_password",
            "text_input_boxes",
            **{"label": "Password", "type": "password"}
        ).render()


        if st.button("login_submit_btn", key="login_submit_button"):
            login_handler.handle_email_login(
                st.session_state["config"]["text_input_boxes"]["login_email"],
                st.session_state["config"]["text_input_boxes"]["login_password"]
            )
            print("we just logged in!")

def display_already_logged_in():
    if st.button("Logout", type="secondary"):
        if login_handler.supabase:
            login_handler.supabase().auth.sign_out()
        st.session_state.pop("user", None)
        st.rerun()
