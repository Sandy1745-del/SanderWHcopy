import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# Laad dataset vanaf GitHub
csv_url = "https://raw.githubusercontent.com/Sandy1745-del/SanderWHcopy/main/sample_data.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(csv_url)
    # Wijzig datum naar dd-mm-yyyy
    df["Datum"] = pd.to_datetime(df["Datum"]).dt.strftime("%d-%m-%Y")
    return df

@st.cache_data
def get_latest_prices(tickers):
    data = {}
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            price = info.get("regularMarketPrice", None)
            if price:
                data[ticker] = price
        except:
            continue
    return data, datetime.utcnow().strftime("%d-%m-%Y %H:%M UTC")

df = load_data()

st.title("🇺🇸 Politiek Aandelen Dashboard")
st.markdown("Geselecteerde transacties van prominente Amerikaanse politici.")

politici = df["Politicus"].unique().tolist()
selectie = st.multiselect("Kies politicus:", opties := politici, default=politici)

filtered = df[df["Politicus"].isin(selectie)]

# Toon huidige koers
tickers = filtered["Aandeel"].unique().tolist()
koersen, timestamp = get_latest_prices(tickers)

st.markdown(f"📈 **Actuele koersen** *(laatst bijgewerkt: {timestamp})*")
for t in tickers:
    prijs = koersen.get(t, "Niet beschikbaar")
    st.markdown(f"- **{t}**: ${prijs}")

st.markdown("### 📊 Geselecteerde transacties")
st.dataframe(filtered)

st.download_button("📥 Download als Excel", filtered.to_csv(index=False), file_name="politiek_aandelen.csv")
