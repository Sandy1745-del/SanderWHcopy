import streamlit as st
import requests
import pandas as pd
import time

# === CONFIG ===
ACTOR_ID = "saswave~capitol-trades-scraper"
API_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs"
RUN_STATUS_URL = "https://api.apify.com/v2/actor-runs/{run_id}"
DATASET_URL = "https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true"

# === UI Setup ===
st.set_page_config(page_title="Capitol Trades Dashboard", layout="wide")
st.title("🏛️ Capitol Trades Dashboard (Debug Mode)")
st.write("Controle op Apify API-token en dataverwerking")

# === API Token uit Secrets ophalen ===
apify_token = st.secrets.get("general", {}).get("apify_token", "")
st.markdown(f"🔐 Apify token gevonden: `{bool(apify_token)}`")

if not apify_token:
    st.error("Apify token ontbreekt. Voeg deze toe via Streamlit Cloud > Edit secrets onder [general].")
    st.stop()

# === Start de Actor op Apify ===
try:
    res = requests.post(API_URL, params={"token": apify_token})
    res.raise_for_status()
    run_id = res.json().get("data", {}).get("id")
except Exception as e:
    st.error(f"❌ Fout bij starten van Apify actor: {e}")
    st.stop()

# === Wachten op voltooiing ===
with st.spinner("⏳ Wachten op Apify actor-run..."):
    status = "RUNNING"
    while status in ["READY", "RUNNING"]:
        time.sleep(2)
        stat_res = requests.get(RUN_STATUS_URL.format(run_id=run_id), params={"token": apify_token})
        status = stat_res.json().get("data", {}).get("status")
        if status == "SUCCEEDED":
            dataset_id = stat_res.json().get("data", {}).get("defaultDatasetId")
            break
    else:
        st.error(f"❌ Actor-run faalde of duurde te lang. Laatste status: {status}")
        st.stop()

# === Data ophalen ===
try:
    df = pd.read_json(DATASET_URL.format(dataset_id=dataset_id))
    st.success("✅ Data succesvol opgehaald van Apify!")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ Fout bij ophalen van dataset: {e}")
