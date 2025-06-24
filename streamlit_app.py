from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Capitol Trades Dashboard", layout="wide")

st.markdown("## 🏛️ Capitol Trades Dashboard")
st.markdown("Bekijk recente aandelenaankopen en -verkopen van Amerikaanse politici.")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("sample_data.csv")
        df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
        df = df[df["Datum"] >= pd.Timestamp("2025-01-01")]
        df = df.sort_values(by="Datum", ascending=False)
        df["Datum"] = df["Datum"].dt.strftime("%d-%m-%Y")
        return df
    except Exception as e:
        st.error(f"Fout bij het laden van data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ Geen data beschikbaar.")
    st.stop()

tickers = df["Aandeel"].unique()

@st.cache_data(ttl=3600)
def fetch_live_prices(tickers):
    prices = {}
    now = datetime.now(pytz.timezone("Europe/Amsterdam")).strftime("%d-%m-%Y %H:%M")
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            price = stock.history(period="1d")["Close"].iloc[-1]
            prices[ticker] = round(price, 2)
        except:
            prices[ticker] = "Onbekend"
    return prices, now

live_prices, timestamp = fetch_live_prices(tickers)

def calculate_returns(df, live_prices):
    df["Aankoopprijs"] = None
    df["Huidige prijs ($)"] = None
    df["Rendement (%)"] =
