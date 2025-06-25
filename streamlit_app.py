
import streamlit as st
import requests
import pandas as pd
import time
import os

st.set_page_config(page_title="Capitol Trades Dashboard", page_icon="🏛️")

st.title("🏛️ Capitol Trades Dashboard")
st.markdown("Recente aandelentransacties van prominente Amerikaanse politici")

# Apify token ophalen
APIFY_TOKEN = st.secrets.get("APIFY_TOKEN") or os.getenv("APIFY_TOKEN")

if not APIFY_TOKEN:
    st.error("❌ APIFY_TOKEN niet gevonden in secrets of omgevingsvariabelen.")
    st.stop()

# CapitolTrades actor
ACTOR_ID = "saswave~capitol-trades-scraper"

@st.cache_data(ttl=3600)
def run_apify_actor():
    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
    payload = {
        "memoryMbytes": 4096,
        "timeoutSecs": 1200,
        "build": "latest",
        "input": {"days": 90}
    }
    run_res = requests.post(run_url, json=payload)
    run_res.raise_for_status()
    run_id = run_res.json()["data"]["id"]

    # Pollen op voltooiing
    for _ in range(30):
        status_res = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}")
        status = status_res.json()["data"]["status"]
        if status == "SUCCEEDED":
            break
        time.sleep(3)
    else:
        raise Exception("Timeout: Apify actor draait nog steeds...")

    # Resultaten ophalen
    dataset_res = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}")
    dataset_res.raise_for_status()
    return pd.DataFrame(dataset_res.json())

# Data ophalen
try:
    df = run_apify_actor()
except Exception as e:
    st.error("❌ Kon geen data ophalen van Apify.")
    st.warning("⚠️ Geen data beschikbaar.")
    st.stop()

if df.empty:
    st.warning("⚠️ Geen resultaten gevonden.")
    st.stop()

# Kolommen standaardiseren
df["politician"] = df["politician"].str.title()
df["ticker"] = df["ticker"].str.upper()
df["transactionDate"] = pd.to_datetime(df["transactionDate"]).dt.date
df["amount"] = df["amount"].astype(str)

# Interface
politici = df["politician"].unique().tolist()
selectie = st.multiselect("Kies politicus:", politici, default=politici)

df_selectie = df[df["politician"].isin(selectie)].sort_values(by="transactionDate", ascending=False)

st.subheader("📄 Geselecteerde transacties")
if df_selectie.empty:
    st.warning("⚠️ Geen data beschikbaar.")
else:
    df_viz = df_selectie[["politician", "ticker", "transactionDate", "type", "amount"]].rename(columns={
        "politician": "Politicus",
        "ticker": "Aandeel",
        "transactionDate": "Datum",
        "type": "Transactie",
        "amount": "Waarde"
    })
    st.dataframe(df_viz, use_container_width=True)
    st.download_button("📥 Download als CSV", df_viz.to_csv(index=False), file_name="capitol_trades.csv")
