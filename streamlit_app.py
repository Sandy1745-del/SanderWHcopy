import streamlit as st
import requests
import pandas as pd
import time

# Constante variabelen
ACTOR_ID = "saswave~capitol-trades-scraper"
API_URL_TEMPLATE = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs"  # Start een nieuwe run
RUNS_STATUS_URL_TEMPLATE = "https://api.apify.com/v2/actor-runs/{run_id}"
RUNS_DATASET_URL_TEMPLATE = "https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true"

# App-layout
st.set_page_config(page_title="Capitol Trades Dashboard", layout="wide")
st.title("\U0001F3DB️ Capitol Trades Dashboard (Debug Mode)")
st.write("Controle op Apify API-token en dataverwerking")

# Token laden uit Streamlit Secrets
apify_token = st.secrets.get("general", {}).get("apify_token", "")
st.markdown(f"**\U0001F510 Apify token gevonden:** `{bool(apify_token)}`")

# Stop als token niet beschikbaar is
if not apify_token:
    st.error("Apify token ontbreekt. Voeg deze toe aan .streamlit/secrets.toml onder [general].")
    st.stop()

# Start de actor-run
try:
    response = requests.post(API_URL_TEMPLATE, params={"token": apify_token})
    response.raise_for_status()
    run_id = response.json().get("data", {}).get("id")
except Exception as e:
    st.error(f"❌ Fout bij starten van Apify actor: {e}")
    st.stop()

# Check runstatus
with st.spinner("⏳ Wachten op Apify actor-run..."):
    status = "RUNNING"
    while status in ["READY", "RUNNING"]:
        time.sleep(2)
        r = requests.get(RUNS_STATUS_URL_TEMPLATE.format(run_id=run_id), params={"token": apify_token})
        status = r.json().get("data", {}).get("status")
        if status == "SUCCEEDED":
            dataset_id = r.json().get("data", {}).get("defaultDatasetId")
            break
    else:
        st.error(f"❌ Actor-run faalde of duurde te lang. Laatste status: {status}")
        st.stop()

# Data ophalen
try:
    df = pd.read_json(RUNS_DATASET_URL_TEMPLATE.format(dataset_id=dataset_id))
    st.success("✅ Data succesvol opgehaald van Apify!")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ Fout bij ophalen van dataset: {e}")
