import ulid
import streamlit as st
from supabase.client import ClientOptions
from supabase import create_client
from src.ui.widgets import MakeWidget
from src.state_management import ConfigManager


@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    options_ = ClientOptions(flow_type="pkce")
    # Tell the client we want the PKCE flow
    return create_client(
        url,
        key,
        options=options_
    )

def add_problem_event():
    problem_id = ulid.new().str
    # (WIP)


class SupabaseLogin:
    def __init__(self):
        self.supabase = st.session_state["supabase_client"]
        self.restore_session()

    def restore_userdata_via_code(self, params):
        code = params["code"]
        try:
            # Exchange the authorization code for a session
            data = self.supabase.auth.exchange_code_for_session({"auth_code": code})


            # Store user and tokens in session state
            st.session_state["user"] = data.user
            st.session_state["supabase_tokens"] = {
                "access_token": data.session.access_token,
                "refresh_token": data.session.refresh_token,
            }

            # Clear the code from URL
            st.query_params.clear()
            print("Retained a login state via code.")
            st.rerun()

        except Exception as e:
            st.error(f"Failed restore userdata via params: {str(e)}")
            st.query_params.clear()

    def restore_userdata_via_token(self):
        try:
            # Set the session using stored tokens
            tokens = st.session_state["supabase_tokens"]
            self.supabase.auth.set_session(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"]
            )

            # Get and store the user
            user_response = self.supabase.auth.get_user()
            if user_response and user_response.user:
                st.session_state["user"] = user_response.user
                print("Retained a login state via token.")


        except Exception as e:
            # Tokens might be expired
            st.session_state.pop("supabase_tokens", None)
            st.session_state.pop("user", None)
            print(f"Failed restore userdata via token: {e}.")

    def restore_userdata_via_cookies(self):
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                st.session_state["user"] = session.user
                # Optionally store tokens
                st.session_state["supabase_tokens"] = {
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                }
                print("Retained a login state via cookies.")
        except Exception as e:
            print(f"Failed restore userdata via refresh token: {e}")
            pass

    def restore_session(self):
        """
        This runs on every page load and handles 3 scenarios:
        1. User just came back from OAuth provider with a code
        2. User has tokens stored in session state (page refresh)
        3. User has Supabase cookies (new session)
        """

        params = st.query_params
        if "code" in params:
            self.restore_userdata_via_code(params)

        elif not st.session_state.get("user") and st.session_state.get("supabase_tokens"):
            self.restore_userdata_via_token()

        elif not st.session_state.get("user"):
            self.restore_userdata_via_cookies()

    def handle_google_login(self):
        """Handle Google OAuth login"""
        if self.supabase:
            try:
                # Redirect to Google OAuth
                try:
                    current_url = st.context.url
                    redirect_url = current_url.split("?")[0]
                except Exception as e:
                    print(f"Failed to get redirect url: {str(e)}: falling back to manual construction.")
                    redirect_url = st.get_option("server.baseUrlPath") or "http://localhost:8501"

                response = self.supabase.auth.sign_in_with_oauth(
                    {
                        "provider": "google",
                        "options": {
                            "flow_type": "pkce",  # ⬅️ new
                            "redirect_to": redirect_url
                        },
                    }
                )
                st.link_button("Continue with Google", url=response.url)
                st.markdown(f'<meta http-equiv="refresh" content="0;url={response.url}">', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Google login failed: {str(e)}")

    def handle_github_login(self):
        """Handle GitHub OAuth login"""
        if self.supabase:
            try:
                # Redirect to GitHub OAuth
                response = self.supabase.auth.sign_in_with_oauth({
                    "provider": "github",
                    "options": {
                        "redirect_to": st.get_option("server.baseUrlPath") or "http://localhost:8501"
                    }
                })
                st.markdown(f'<meta http-equiv="refresh" content="0;url={response.url}">', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"GitHub login failed: {str(e)}")

    def handle_email_login(self, email, password):
        """Handle email/password login"""
        if self.supabase and email and password:
            try:
                response = self.supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state["user"] = response.user
                st.success("Login successful!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")

    def display_already_logged_in(self):
        # col1, col2 = st.columns([3, 1])
        if False: # keep this for now...
            with col1:
                st.success(f"Logged in as: {st.session_state['user'].email}")
            with col2:
                if st.button("Logout", type="secondary"):
                    if self.supabase:
                        self.supabase.auth.sign_out()
                    st.session_state.pop("user", None)
                    st.rerun()
            return

        if st.button("Logout", type="secondary"):
            if self.supabase:
                self.supabase.auth.sign_out()
            st.session_state.pop("user", None)
            st.rerun()


    def display_login(self):

        col1, col2, col3  = st.columns([1,1,1], vertical_alignment="center")
        google_logo = "https://www.gstatic.com/images/branding/product/1x/googleg_32dp.png"
        github_logo = "https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png"

        with col1:
            st.markdown(f"<span style='font-size:36px;'>{":material/key:"}</span>", unsafe_allow_html=True)
        with col2:
            if st.button(f"![Google]({google_logo})", key="google_login_btn"):
                self.handle_google_login()
        if False:
            with col3:
                if st.button(f"![GitHub]({github_logo})", key="github_login_btn"):
                    self.handle_google_login()


        st.divider()

        if False:
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
                self.handle_email_login(
                    st.session_state["config"]["text_input_boxes"]["login_email"],
                    st.session_state["config"]["text_input_boxes"]["login_password"]
                )
                print("we just logged in!")

    def render(self):
        """Render the login component"""

        if st.session_state.get("user"):
            self.display_already_logged_in()
            return

        self.display_login()



