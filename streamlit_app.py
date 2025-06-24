import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz
import requests

# Lijst prominente politici
PROMINENTE_POLITICI = [
    "Nancy Pelosi", "Dan Crenshaw", "Tommy Tuberville", "Ro Khanna", "Josh Hawley"
]

# Laad Apify-token uit .secrets (vereist configuratie op Streamlit Cloud)
API_URL = "https://api.apify.com/v2/actor-tasks/YOUR_TASK_ID/runs/last/dataset/items?token=YOUR_TOKEN"

@st.cache_data(ttl=3600)
def laad_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            return df
        else:
            st.error("Kon geen data ophalen van Apify.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Fout bij ophalen data: {e}")
        return pd.DataFrame()

def filter_dataframe(df):
    df = df[df["politician"].isin(PROMINENTE_POLITICI)]
    df["date"] = pd.to_datetime(df["date"])
    df["datum"] = df["date"].dt.strftime("%d-%m-%Y")
    df["type"] = df["type"].str.capitalize().replace({"Purchase": "Koop", "Sale": "Verkoop"})
    return df[["politician", "ticker", "datum", "type", "amount", "asset"]]

def voeg_actuele_koers_toe(df):
    unieke_tickers = df["ticker"].dropna().unique()
    koersen = {}
    for ticker in unieke_tickers:
        try:
            koers = yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]
            koersen[ticker] = round(koers, 2)
        except:
            koersen[ticker] = None
    df["Actuele koers ($)"] = df["ticker"].map(koersen)
    return df

def main():
    st.set_page_config("Capitol Trades", page_icon="🏛️", layout="wide")
    st.title("🏛️ Capitol Trades Dashboard")
    st.write("Recente aandelentransacties van prominente Amerikaanse politici")

    df_raw = laad_data()
    if df_raw.empty:
        st.warning("⚠️ Geen data beschikbaar.")
        return

    df = filter_dataframe(df_raw)
    df = voeg_actuele_koers_toe(df)

    selectie = st.multiselect("Selecteer politicus", PROMINENTE_POLITICI, default=PROMINENTE_POLITICI)
    gefilterd = df[df["politician"].isin(selectie)]

    if gefilterd.empty:
        st.warning("⚠️ Geen resultaten voor deze selectie.")
    else:
        st.dataframe(gefilterd, use_container_width=True)

        csv = gefilterd.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download als CSV", csv, "capitoltrades.csv", "text/csv")

if __name__ == "__main__":
    main()
