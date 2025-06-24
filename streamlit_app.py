import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz

st.set_page_config(page_title="Capitol Trades Dashboard", layout="wide")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("sample_data.csv")
        df["Datum"] = pd.to_datetime(df["Datum"])
        df = df[df["Datum"] >= pd.to_datetime("2025-01-01")]
        df = df.sort_values("Datum", ascending=False)
        return df
    except Exception as e:
        st.error(f"❌ Fout bij laden van data: {e}")
        return pd.DataFrame()

def fetch_current_prices(tickers):
    prices = {}
    for ticker in tickers:
        try:
            ticker_data = yf.Ticker(ticker)
            df = ticker_data.history(period="1d")
            price = df["Close"].iloc[-1]
            prices[ticker] = price
        except:
            prices[ticker] = None
    return prices

def kleur(val):
    if pd.isna(val): return ""
    return "color: green;" if val > 0 else "color: red;"

# UI
st.title("🏛️ Capitol Trades Dashboard")
df = load_data()

if df.empty:
    st.warning("⚠️ Geen data beschikbaar.")
    st.stop()

unieke_tickers = df["Aandeel"].dropna().unique().tolist()
koersen = fetch_current_prices(unieke_tickers)

# Prijs + rendement toevoegen
df["Actuele prijs ($)"] = df["Aandeel"].map(koersen)
df["Aankoopprijs ($)"] = pd.to_numeric(df["Waarde ($)"], errors="coerce")
df["Rendement (%)"] = ((df["Actuele prijs ($)"] - df["Aankoopprijs ($)"]) / df["Aankoopprijs ($)"] * 100).round(2)
df["Actuele prijs ($)"] = df["Actuele prijs ($)"].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
df["Aankoopprijs ($)"] = df["Aankoopprijs ($)"].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")

# Tijdstempel
amsterdam = pytz.timezone("Europe/Amsterdam")
nu = datetime.now(amsterdam).strftime("%d-%m-%Y %H:%M:%S")
st.caption(f"Laatst bijgewerkt: {nu} (Europe/Amsterdam tijd)")

# Vertaal transactie
df["Transactie"] = df["Transactie"].replace({
    "purchase": "Koop",
    "sale_full": "Verkoop",
    "sale_partial": "Verkoop"
})

# Kolommen herschikken
kolommen = ["Politicus", "Aandeel", "Datum", "Transactie", "Aankoopprijs ($)", "Actuele prijs ($)", "Rendement (%)"]
df = df[kolommen]
df = df.sort_values("Datum", ascending=False)

# Tabel tonen
st.dataframe(df.style.applymap(kleur, subset=["Rendement (%)"]), use_container_width=True)

# Downloadknop
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download CSV", data=csv, file_name="capitol_trades_dashboard.csv", mime="text/csv")
