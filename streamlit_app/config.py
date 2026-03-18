"""Configuration for the DONS Cloud Migration Platform Streamlit app."""

import os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
