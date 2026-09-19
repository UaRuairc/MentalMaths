import os

import streamlit as st
from supabase import Client, create_client
from supabase.client import ClientOptions


def _get_secret(name: str) -> str | None:
    """Read a secret from st.secrets, falling back to an environment variable.

    Returns None instead of raising when the secret isn't set anywhere.
    """
    try:
        value = st.secrets.get(name)
    except FileNotFoundError:
        # No secrets.toml exists at all. Streamlit raises
        # StreamlitSecretNotFoundError, a subclass of FileNotFoundError,
        # even for .get().
        value = None
    return value or os.getenv(name)


@st.cache_resource
def init_connection() -> Client | None:
    """Create the Supabase client, or return None if it isn't configured."""
    print("init connection")
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY")

    if not url or not key:
        print("SUPABASE_URL / SUPABASE_KEY not set; running without Supabase.")
        return None

    options_ = ClientOptions(
        flow_type="pkce",  # Tell the client we want the PKCE flow
        auto_refresh_token=True,
        persist_session=True,
    )
    try:
        return create_client(url, key, options=options_)
    except Exception as e:  # e.g. malformed URL or key
        print(f"Could not create Supabase client: {e}")
        return None


def get_supabase() -> Client | None:
    """Return the Supabase client, or None if Supabase isn't configured."""
    if "supabase_client" not in st.session_state:
        raise RuntimeError(
            "Supabase client is not in the session state. "
            "It should have been initialised on application startup."
        )
    return st.session_state["supabase_client"]


def supabase_enabled() -> bool:
    """True if a working Supabase client is available."""
    return st.session_state.get("supabase_client") is not None