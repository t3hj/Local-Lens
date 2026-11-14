import streamlit as st

from supabase import create_client

from config.settings import SUPABASE_KEY, SUPABASE_URL


def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Supabase credentials are missing. Set SUPABASE_URL and SUPABASE_KEY in .streamlit/secrets.toml"
        )

    # Auth mutates the client; sharing it across visitors can mix identities.
    if "_ll_supabase_client" not in st.session_state:
        st.session_state["_ll_supabase_client"] = create_client(SUPABASE_URL, SUPABASE_KEY)
    return st.session_state["_ll_supabase_client"]
