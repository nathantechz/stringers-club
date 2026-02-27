import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        # Try Streamlit Cloud secrets first, then fall back to env vars / .env
        try:
            import streamlit as st
            url = st.secrets.get("SUPABASE_URL", "") or os.environ.get("SUPABASE_URL", "")
            key = st.secrets.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
        except Exception:
            url = os.environ.get("SUPABASE_URL", "")
            key = os.environ.get("SUPABASE_KEY", "")

        if not url or not key:
            raise ValueError(
                "Missing SUPABASE_URL or SUPABASE_KEY. "
                "Add them to .streamlit/secrets.toml or your .env file."
            )
        _client = create_client(url, key)
    return _client
