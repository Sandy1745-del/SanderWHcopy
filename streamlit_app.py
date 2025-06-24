import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime
import pytz
import os

st.set_page_config(page_title="Politiek Aandelen Dashboard", layout="wide")

# ─── Fallback logica ─────────────────────────────────────────────────────────────

def try_fetch_live_data():
    try:
        url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = pd.DataFrame(response.json())
            return data, "✅ Live data succesvol geladen"
        else:
            return None, "⚠️ Live API niet bereikbaar – backup gebruikt"
    except:
        return None, "⚠️ Live API niet beschikbaar – backup gebruikt"

@st.cache_data
def load_data():
    data, status = try_fetch_live_data()
    if data is None or data.empty:
        if os.path.exists("sample_data.csv"):
            data = pd.read_csv("sample_data.csv", parse_dates=["transaction_date"])
        else:
            st.error("Geen live data of sample_data.csv beschikbaar.")
            st.stop()
    return data, status

@st.cache_data
def get_current_prices(tickers):
    prices = {}
    try:
        data = yf.download(tickers=tickers, period="1d", progress=False, group_by='ticker')
        if len(tickers) == 1:
            prices[tickers[0]] = round(data["Close"].iloc[-1], 3)
        else:
            for ticker in tickers:
                try:
                    prices[ticker] = round(data[ticker]["Close"].iloc[-1], 3)
                except:
                    continue
    except:
        pass
    return prices

# ─── Data verwerken ──────────────────────────────────────────────────────────────

df, status_message = load_data()

# Filters en vertalingen
df = df[df["transaction_date"].notna()]
df = df[df["asset_description"].notna()]
df = df[~df["asset_description"].str.contains(" ")]
df = df[df["asset_description"].str.len() <= 5]
df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
df = df[df["transaction_date"] >= datetime(2025, 1, 1)]

df["Datum"] = df["transaction_date"].dt.strftime("%d-%m-%Y")
df["Aandeel"] = df["asset_description"].str.upper()
df["Politicus"] = df["representative"]
df["Transactie"] = df["type"].map({
    "purchase": "Koop",
    "sale_full": "Verkoop",
    "sale_partial": "Verkoop"
}).fillna("Onbekend")
df["Waarde ($)"] = df["amount"]

# ─── Koersen en rendement berekenen ──────────────────────────────────────────────

tickers = df["Aandeel"].unique().tolist()
koersen = get_current_prices(tickers)

df["Aankoopprijs ($)"] = "-"
df["Actuele prijs ($)"] = "-"
df["Rendement (%)"] = "-"

for i, row in df.iterrows():
    ticker = row["Aandeel"]
    try:
        hist = yf.download(ticker, period="6mo", progress=False)
        tx_date = row["transaction_date"]
        tx_date = hist.index[hist.index.get_indexer([tx_date], method='nearest')[0]]
        aankoop = hist.loc[tx_date]["Close"]
        actueel = koersen.get(ticker, None)
        if actueel:
            rendement = ((actueel - aankoop) / aankoop) * 100
            df.at[i, "Aankoopprijs ($)"] = f"${round(aankoop, 2)}"
            df.at[i, "Actuele prijs ($)"] = f"${round(actueel, 2)}"
            df.at[i, "Rendement (%)"] = round(rendement, 2)
    except:
        continue

df = df.sort_values("transaction_date", ascending=False)

# ─── UI ──────────────────────────────────────────────────────────────────────────

st.title("🇺🇸 Politiek Aandelen Dashboard")
st.markdown(status_message)

if df.empty or "Politicus" not in df.columns:
    st.warning("⚠️ Geen geldige data.")
    st.stop()

politici = df["Politicus"].unique()
selectie = st.multiselect("Kies politicus:", sorted(politici), default=politici[:4])
filtered = df[df["Politicus"].isin(selectie)].copy()

# Tijden
amsterdam_time = datetime.now(pytz.timezone("Europe/Amsterdam")).strftime("%d-%m-%Y %H:%M")

st.markdown(f"📉 **Actuele koersen** _(USD, laatst bijgewerkt: {amsterdam_time} Amsterdamse tijd)_")

for ticker in sorted(set(filtered["Aandeel"])):
    prijs = koersen.get(ticker)
    if prijs:
        st.markdown(f"- **{ticker}**: **${prijs}**")

def kleur_rendement(val):
    try:
        if float(val) > 0:
            return "color: green;"
        elif float(val) < 0:
            return "color: red;"
    except:
        return ""
    return ""

kolommen = [
    "Politicus", "Aandeel", "Datum", "Transactie", "Waarde ($)",
    "Aankoopprijs ($)", "Actuele prijs ($)", "Rendement (%)"
]

st.markdown("📊 **Geselecteerde transacties**")
styled_df = filtered[kolommen].style.applymap(kleur_rendement, subset=["Rendement (%)"])
st.dataframe(styled_df, use_container_width=True)

csv = filtered[kolommen].to_csv(index=False).encode("utf-8")
st.download_button("📩 Download als Excel", csv, "transacties.csv", "text/csv")
