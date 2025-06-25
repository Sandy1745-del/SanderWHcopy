import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Actor en API-token ophalen
ACTOR_ID = "saswave~capitol-trades-scraper"
API_TOKEN = st.secrets["apify"]["token"]
RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={API_TOKEN}&memory=1024&timeout=120"

st.set_page_config(page_title="Capitol Trades", page_icon="🏛️", layout="wide")
st.title("🏛️ Capitol Trades Dashboard (Debug Mode)")
st.caption("Controle op Apify API-token en dataverwerking")

# Debug info
st.write("🔐 Apify token gevonden:", API_TOKEN is not None)

# Actor starten
with st.spinner("⏳ Start Apify actor en wacht op data..."):
    try:
        start_res = requests.post(RUN_URL)
        start_res.raise_for_status()
        run_id = start_res.json()["data"]["id"]

        # Pollen tot voltooiing
        STATUS_URL = f"https://api.apify.com/v2/actor-runs/{run_id}?token={API_TOKEN}"
        DATASET_URL = f"https://api.apify.com/v2/datasets/{run_id}/items?format=json&clean=true&token={API_TOKEN}"

        status = "RUNNING"
        while status in ["READY", "RUNNING"]:
            time.sleep(2)
            poll = requests.get(STATUS_URL).json()
            status = poll["data"]["status"]
            st.write(f"📡 Status: {status}")

        if status != "SUCCEEDED":
            st.error(f"❌ Run mislukt: {status}")
        else:
            df = pd.read_json(DATASET_URL)
            st.success("✅ Data opgehaald van Apify!")
            st.dataframe(df)

    except Exception as e:
        st.error(f"❌ Fout bij starten van Apify actor: {e}")
