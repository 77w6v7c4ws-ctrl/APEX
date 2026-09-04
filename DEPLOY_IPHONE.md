# Deploy APEX to iPhone with Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload every file/folder from APEX_IPHONE_READY into the repository.
3. Do NOT upload a real `.streamlit/secrets.toml`.
4. Open Streamlit Community Cloud.
5. Create a new app from your repository.
6. Main file path: `app.py`
7. Open Advanced settings.
8. Use Python 3.12.
9. Paste secrets like:

THE_ODDS_API_KEY = "your_real_key"
APEX_PLAYER_HISTORY_URL = ""
APEX_AVAILABILITY_URL = ""

10. Deploy.
11. Open the generated `*.streamlit.app` page on iPhone Safari.
12. Tap Share -> Add to Home Screen.

The STATUS tab inside APEX will show whether live odds and optional data feeds are connected.
