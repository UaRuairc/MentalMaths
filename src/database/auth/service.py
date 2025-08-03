import streamlit as st
from streamlit_cookies_controller import CookieController
from src.utils import file_log
from src.database.connection import get_supabase
from requests.exceptions import HTTPError
import json
import time
from datetime import datetime, timedelta
COOKIE_NAME  = "sb_tokens"
COOKIE_AGE   = 60 * 60 * 24 * 30

class SupabaseLogin:
    def __init__(self):
        self.instance_id = id(self)

    @staticmethod
    def supabase():
        # Single source of truth always
        return get_supabase()

    @staticmethod
    def save_tokens_as_cookie(cookie_manager: CookieController):
        print("saving cookie")
        cookie_manager.set(
            "sb_tokens",
            json.dumps(st.session_state["tokens_to_save"]),
            expires=datetime.utcnow() + timedelta(days=30),
            path="/",
            secure=st.context.url.startswith("https"),
        )
        st.session_state["tokens_to_save"] = None

    @staticmethod
    def already_logged_in():
        is_logged_in = st.session_state.get("user") is not None
        return is_logged_in

    def restore_userdata_via_query_params(self, params):
        code = params["code"]
        for attempt in range(2):
            try:
                return self.supabase().auth.exchange_code_for_session({"auth_code": code})
            except HTTPError as e:
                status = e.response.status_code
                # Retry once on that known “404 / invalid flow” case
                if status == 404 and attempt == 0:
                    file_log("Login session expired — click the button again (retrying once)…")
                    time.sleep(0.1)
                    continue
                # Otherwise, give up
                file_log(f"OAuth failed (HTTP {status}): {e}")
                return False


            except Exception as e:
                file_log(f"Unexpected error during OAuth: {e}")
                return False
        file_log("OAuth failed after retry — giving up.")
        return False

    def restore_userdata_via_tokens(self):
        try:
            # Set the session using stored tokens
            file_log("TRY: restoring userdata via tokens!!!")
            tokens = st.session_state["supabase_tokens"]
            file_log(tokens)
            self.supabase().auth.set_session(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"]
            )
            st.session_state["expired_tokens"] = st.session_state["supabase_tokens"].copy()
            st.session_state["supabase_tokens"] = None

            # Get and store the user
            user_response = self.supabase().auth.get_user()
            if user_response and user_response.user:
                st.session_state["user"] = user_response.user
                print("Retained a login state via token.")

            return True

        except Exception as e:
            # Tokens might be expired
            st.session_state["expired_tokens"] = st.session_state["supabase_tokens"].copy()
            st.session_state["supabase_tokens"] = None
            file_log(f"Failed restore userdata via token: {e}.")
            return False

    def restore_tokens_via_cookies(self):
        try:
            cookie = st.session_state["cookies"].get(COOKIE_NAME)
            if not cookie:
                file_log(f"could not find a cookie named {COOKIE_NAME}, if you see this after the line 'Creating and storing cookies now...' then persistence failed!")
                return

            if cookie is not None and cookie != st.session_state["expired_tokens"]:
                st.session_state["supabase_tokens"] = cookie
                file_log("Obtained tokens via cookies.")
            else:
                file_log("Tokens found were expired, not keeping.")
            return True

        except Exception as e:
            file_log(f"Failed restore userdata via cookies: {e}")
            return False

    def try_login(self):
        """provider can be either google, GitHub or email"""
        if "try_login" in st.session_state and st.session_state["try_login"]:
            provider = st.session_state["try_login"]
            login_method = f"handle_{provider}_login"
            handler = getattr(self, login_method, None)

            # set to false now
            st.session_state["try_login"] = False

            if callable(handler):
                handler()
                return True
        return False

    def attempt_user_restoration(self, cookie_manager, are_cookies_ready=False):

        if "code" in st.query_params and not st.session_state["did_try_restore"] and isinstance(
                st.session_state["cookies"],
                dict):
            st.session_state["did_try_restore"] = True
            data = self.restore_userdata_via_query_params(st.query_params)
            st.session_state["user"] = data.user
            st.session_state["tokens_to_save"] = {
                "access_token": data.session.access_token,
                "refresh_token": data.session.refresh_token,
            }
            st.query_params.clear()

        elif "code" in st.query_params and st.session_state["did_try_restore"]:
            file_log("already tried restoring via query params during this session, not trying again.")

        if are_cookies_ready and self.restore_tokens_via_cookies() and st.session_state[
            "supabase_tokens"] is not None:
            cookies_successful = self.restore_userdata_via_tokens()
            # reset some variables
            if cookies_successful:
                st.session_state["try_google_login"] = False

        if "tokens_to_save" in st.session_state and st.session_state["tokens_to_save"] is not None:
            self.save_tokens_as_cookie(cookie_manager)

        is_successful_restoration = st.session_state.get("user") is not None

        return is_successful_restoration

    def handle_google_login(self):
        """Handle Google OAuth login"""
        file_log("handling google login")
        if self.supabase():
            try:
                # Redirect to Google OAuth
                try:
                    current_url = st.context.url
                    redirect_url = current_url.split("?")[0]
                except Exception as e:
                    print(f"Failed to get redirect url: {str(e)}: falling back to manual construction.")
                    redirect_url = st.get_option("server.baseUrlPath") or "http://localhost:8501"

                response = self.supabase().auth.sign_in_with_oauth(
                    {
                        "provider": "google",
                        "options": {
                            "flow_type": "pkce",  # ⬅️ new
                            "redirect_to": redirect_url
                        },
                    }
                )
                # st.link_button("Continue with Google", url=response.url)
                file_log("redirecting user to login page")
                st.markdown(f'<meta http-equiv="refresh" content="0;url={response.url}">', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Google login failed: {str(e)}")

    def handle_github_login(self):
        """Handle GitHub OAuth login"""
        if self.supabase():
            try:
                # Redirect to GitHub OAuth
                response = self.supabase().auth.sign_in_with_oauth({
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
        if self.supabase() and email and password:
            try:
                response = self.supabase().auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state["user"] = response.user
                st.success("Login successful!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")


