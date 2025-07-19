import streamlit as st
from supabase.client import ClientOptions
from supabase import create_client

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

def get_supabase():
    try:
        return st.session_state["supabase_client"]
    except KeyError:
        raise RuntimeError("Supabase client is not in the session state. It should have been initialised on application startup.")
