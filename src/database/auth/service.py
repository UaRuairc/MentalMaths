import streamlit as st
from src.database.connection import get_supabase

class SupabaseLogin:
    def __init__(self):
        self.restore_session()

    @staticmethod
    def supabase():
        # Single source of truth always
        return get_supabase()

    def restore_userdata_via_code(self, params):
        code = params["code"]
        try:
            # Exchange the authorization code for a session
            data = self.supabase().auth.exchange_code_for_session({"auth_code": code})


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
            self.supabase().auth.set_session(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"]
            )

            # Get and store the user
            user_response = self.supabase().auth.get_user()
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
            session = self.supabase().auth.get_session()
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
                st.link_button("Continue with Google", url=response.url)
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


