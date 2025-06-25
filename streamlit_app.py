
import streamlit as st
import requests
import pandas as pd
import time
import os

st.set_page_config(page_title="Capitol Trades Debug", page_icon="🔍")

st.title("🏛️ Capitol Trades Dashboard (Debug Mode)")
st.markdown("Controle op Apify API-token en dataverwerking")

# Haal Apify token op uit secrets of omgevingsvariabele
APIFY_TOKEN = st.secrets.get("APIFY_TOKEN") or os.getenv("APIFY_TOKEN")
st.write("🔐 Apify token gevonden:", bool(APIFY_TOKEN))

if not APIFY_TOKEN:
    st.error("❌ APIFY_TOKEN niet ingesteld.")
    st.stop()

# Gebruik publieke Apify actor
ACTOR_ID = "lukasss~congress-stock-trades"

def run_apify_actor():
    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
    payload = {"memoryMbytes": 4096, "timeoutSecs": 1200, "build": "latest", "input": {"days": 90}}

    try:
        run_res = requests.post(run_url, json=payload)
        run_res.raise_for_status()
        run_id = run_res.json()["data"]["id"]
        st.write("🚀 Actor gestart. Run ID:", run_id)
    except Exception as e:
        st.error(f"❌ Fout bij starten van Apify actor: {e}")
        st.stop()

    # Wachten op voltooiing
    for attempt in range(30):
        time.sleep(3)
        check_res = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}")
        status = check_res.json()["data"]["status"]
        st.write(f"⌛ Poging {attempt+1}: Status = {status}")
        if status == "SUCCEEDED":
            break
    else:
        st.error("❌ Timeout: actor is niet binnen 90 seconden voltooid.")
        st.stop()

    # Data ophalen
    data_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}"
    try:
        data_res = requests.get(data_url)
        data_res.raise_for_status()
        data = data_res.json()
        st.write("📦 Aantal records ontvangen:", len(data))
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Fout bij ophalen dataset: {e}")
        st.stop()

# Ophalen data
df = run_apify_actor()

if df.empty:
    st.warning("⚠️ Geen resultaten ontvangen van Apify.")
    st.stop()

df["politician"] = df["politician"].str.title()
df["ticker"] = df["ticker"].str.upper()
df["transactionDate"] = pd.to_datetime(df["transactionDate"]).dt.date

# UI
politici = df["politician"].unique().tolist()
selectie = st.multiselect("👤 Kies politicus:", politici, default=politici)

df_selectie = df[df["politician"].isin(selectie)].sort_values(by="transactionDate", ascending=False)

st.subheader("📊 Geselecteerde transacties")
st.dataframe(df_selectie)
