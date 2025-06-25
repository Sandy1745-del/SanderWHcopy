import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Capitol Trades - Pelosi", layout="wide")
st.title("🏛️ Capitol Trades: Nancy Pelosi")

# 🔐 Apify token ophalen
APIFY_TOKEN = st.secrets.get("APIFY_TOKEN", None)

if not APIFY_TOKEN:
    st.error("❌ Geen Apify token gevonden in je Streamlit secrets.")
    st.stop()
else:
    st.success("✅ Apify token gevonden.")

# 🎯 Actorinstellingen
ACTOR_ID = "saswave~capitol-trades-scraper"
RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
HEADERS = {"Content-Type": "application/json"}

# 📤 Input voor deze actor (Nancy Pelosi standaard)
payload = {
    "startUrls": [
        {
            "url": "https://www.capitoltrades.com/trades?politician=Pelosi-Nancy"
        }
    ],
    "maxPagesPerRun": 1,
    "maxItems": 50
}

# ▶️ Actor starten
try:
    start_resp = requests.post(RUN_URL, headers=HEADERS, json=payload)
    start_resp.raise_for_status()
    run_id = start_resp.json()["data"]["id"]
    st.info("⏳ Actor gestart. Data wordt opgehaald...")

    # ⏱ Poll op status
    for _ in range(30):
        status = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}", headers=HEADERS).json()["data"]
        if status["status"] == "SUCCEEDED":
            dataset_id = status["defaultDatasetId"]
            break
        elif status["status"] in ["FAILED", "ABORTED"]:
            st.error(f"❌ Actor status: {status['status']}")
            st.stop()
        time.sleep(2)
    else:
        st.error("❌ Timeout: Apify actor gaf geen resultaat.")
        st.stop()

    # 📥 Haal resultaten op
    data_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"
    df = pd.read_json(data_url)

    if df.empty:
        st.warning("⚠️ Geen data gevonden.")
    else:
        st.success("✅ Data geladen van Apify!")
        st.dataframe(df)

except Exception as e:
    st.error(f"❌ Fout tijdens ophalen van data: {e}")
