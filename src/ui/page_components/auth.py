import streamlit as st
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer
from src.database.auth.service import SupabaseLogin
from src.config.config_management import ConfigManager
from src.ui.widgets import MakeWidget
from src.utils import file_log
ENABLE_GOOGLE_LOGIN = True
ENABLE_GITHUB_LOGIN = False
ENABLE_EMAIL_LOGIN = False

def user_auth():
    """
    auth logic:

    First: try to render "already logged in ui" if
    1. The user logged in already
    2. or: we can restore login info via query params or cookies

    Second: try to log the user in if
    1. They asked to log in

    Third: try to render "display_auth_login_ui" if:
    1. We have already tried to login via other means and it failed

    ASIDE: SOME COMMENTS ABOUT THIS AUTH FLOW, AND WHY MAY END UP NOT USING IT:

    This flow is designed to maintain updated Google tokens in browser cookies at all times.

    In theory, we could use an alternative method, Method 2: use the query params on the initial login to immediately create
    a Supabase session that persists page reloads, app refresh, st session state resetting etc, no manual cookie
    modification is needed as Supabase handles it all nicely.

    Method 2 may just be better than the current 'make cookie with Google tokens' Method. This is because:

    1. Streamlit's lacking of decent cookie support means we need to use a custom React widget which causes reruns.
    2. You should not have reruns queued before events that trigger them immediately if you intend to do anything else
    importing during that run. For example, you can't queue a rerun, do an http request and store data in session state
    because the program ends after the http request

    So you need to make sure you trigger the rerun prior to the request. If you ALWAYS queue a rerun before an HTTP request
    you will NEVER be able to use that data.

    For example, if you have

                <code that queues a rerun every time>

                if no_rerun_queued and want_to_make_http_request:
                    <make http request>
                else:
                    st.rerun()

    you will just be in an infinite loop.

    However, if you have:

                <code that queues a rerun sometimes>

                if no_rerun_queued and want_to_make_http_request:
                    make http request
                else:
                    st.rerun()

    you may eventually get out of the loop.

    This is very ugly though and currently has a bug where pathological cookie states can result
    in too many reruns. Need to improve the logic below.

    Right now, we use Method 1, but may just move to Method 2. Benefit of Method 1 is that if we ever do need Google login
    again, we don't need to prompt them again. Plus, streamlit might just get better cookie support soon, or we could use
    a different UI framework.


    """

    login_container = st.container(key="login")

    cookie_manager = CookieController()
    RemoveEmptyElementContainer()
    are_cookies_ready = isinstance(st.session_state["cookies"], dict)
    login_handler = SupabaseLogin()

    logged_in = login_handler.already_logged_in() or login_handler.attempt_user_restoration(cookie_manager, are_cookies_ready)
    if logged_in:
        display_already_logged_in_placeholder(login_handler, container=login_container)
        file_log("logged in")
        return

    if login_handler.try_login():
        return

    if are_cookies_ready:
        display_auth_login_ui()

    return

def display_auth_login_ui():

    col1, col2, col3  = st.columns([1 ,1 ,1], vertical_alignment="center")
    google_logo = "https://www.gstatic.com/images/branding/product/1x/googleg_32dp.png"
    github_logo = "https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png"

    if ENABLE_GOOGLE_LOGIN:
        with col1:
            st.markdown(f"<span style='font-size:36px;'>{":material/key:"}</span>", unsafe_allow_html=True)
        with col2:
            container = st.container()
            with container:
                st.button(f"![Google]({google_logo})", key="google_login_btn", on_click=flag_login, args=("google",))


    if ENABLE_GITHUB_LOGIN:
        with col3:
            container = st.container()
            with container:
                st.button(f"![GitHub]({github_logo})", key="github_login_btn", on_click=flag_login, args=("github",))

    st.divider()

    if ENABLE_EMAIL_LOGIN:
        st.markdown("**Or login with email**")

        # Email/Password login
        ConfigManager.register("login_email", "text_input_boxes",
                               **{"label": "Email", "placeholder": "your@email.com"})
        MakeWidget(
            "login_email",
            "text_input_boxes",
        ).render()
        ConfigManager.register("login_password", "text_input_boxes",
                               **{"label": "Email", "placeholder": "password"})
        MakeWidget(
            "login_password",
            "text_input_boxes",
            **{"label": "Password", "type": "password"}
        ).render()

        with container:
            st.button("login_email_button", key="login_submit_button", on_click=flag_login, args=("email",))

def display_already_logged_in_placeholder(login_handler, container=st.container):
    with container:
        if st.button("Logout", type="secondary"):
            if login_handler.supabase:
                login_handler.supabase().auth.sign_out()
            st.session_state.pop("user", None)
            login_handler.is_user_logged_in = False
            st.rerun()

def flag_login(provider):
    file_log(f"user wants to login via: {provider}")
    st.session_state["try_cookies"] = True
    st.session_state[f"try_login"] = provider
