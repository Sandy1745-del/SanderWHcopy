import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Capitol Trades", layout="wide")

st.markdown("## 🏛️ Capitol Trades Dashboard (Debug Mode)")
st.markdown("Controle op Apify API-token en dataverwerking")

# Haal Apify token op uit Streamlit secrets
APIFY_TOKEN = st.secrets.get("APIFY_TOKEN", None)

if not APIFY_TOKEN:
    st.error("❌ Geen Apify token gevonden in Streamlit secrets.")
    st.stop()
else:
    st.markdown(f"🔐 Apify token gevonden: <span style='color: green'>True</span>", unsafe_allow_html=True)

# Actor config
ACTOR_ID = "lukass~congress-stock-trades"
RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
HEADERS = {"Content-Type": "application/json"}

try:
    # Start de actor
    run_response = requests.post(RUN_URL, headers=HEADERS)
    run_response.raise_for_status()
    run_id = run_response.json()["data"]["id"]

    st.success("✅ Apify actor gestart")

    # Poll voor resultaat
    result = None
    for _ in range(20):
        time.sleep(5)
        status_resp = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}", headers=HEADERS)
        status_resp.raise_for_status()
        status_data = status_resp.json()["data"]
        if status_data["status"] == "SUCCEEDED":
            result = status_data
            break
        elif status_data["status"] in ["FAILED", "ABORTED", "TIMED-OUT"]:
            raise Exception(f"Run status: {status_data['status']}")

    if not result:
        raise TimeoutError("⏱️ Timeout: Apify actor gaf geen tijdig resultaat.")

    # Haal dataset ID op
    dataset_id = result["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"
    df = pd.read_json(dataset_url)

    if df.empty:
        st.warning("⚠️ Geen data beschikbaar.")
        st.stop()

    st.success("✅ Data succesvol geladen!")
    st.dataframe(df)

except Exception as e:
    st.error(f"❌ Fout bij starten van Apify actor: {e}")
