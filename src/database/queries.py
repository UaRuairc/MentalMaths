from src.database.connection import get_supabase
import streamlit as st


class Queries:
    """
    A class to handle database queries using the Supabase client.
    """
    def __init__(self, client=None):
        self.db = client if client is not None else get_supabase()


    def fetch(self, table_name, cols: str= "*", anon=False, limit=1):
        if anon:
            user_id = "null"
        else:
            user_id = self.get_user_id()

        response = self.db.schema("api").from_(table_name).select("*").limit(limit).is_("user_id", user_id).execute()


        return response

    def fetch_session(self, cols: str= "*", anon=False, limit=1):
        if anon:
            user_id = "null"
        else:
            user_id = self.get_user_id()

        table_name = "game_sessions"
        response = self.db.schema("api").from_(table_name).select("*").limit(limit).is_("user_id", user_id).execute()


        return response

    def fetch_problems(self, session_id, limit=999):

        table_name = "problem_events"
        response = self.db.schema("api").from_(table_name).select("*").limit(limit).eq("session_id", session_id).execute()

        return response




    @staticmethod
    def get_user_id():
        return st.session_state["supabase_client"].auth.get_user().user.id if st.session_state.get("user") is not None else None

    @staticmethod
    def get_session_id():
        """
        Get the current session ID from the session state.
        """
        return st.session_state.get("session_id", None)