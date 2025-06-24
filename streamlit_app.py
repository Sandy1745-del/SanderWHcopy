import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta

@st.cache_data
def fetch_trades():
    url = "https://housestockwatcher.com/api/financial-disclosures"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return []

@st.cache_data
def load_data():
    trades = fetch_trades()
    records = []
    tickers = set()

    for item in trades:
        ticker = item.get("assetDescription", "").strip().upper()
        if len(ticker) > 6 or " " in ticker:
            continue
        try:
            date = datetime.strptime(item["transactionDate"], "%Y-%m-%d")
        except:
            continue
        record = {
            "Politicus": item.get("representative", "Onbekend"),
            "Aandeel": ticker,
            "Datum": date.strftime("%d-%m-%Y"),
            "RawDatum": date,
            "Transactie": item.get("type", "Onbekend"),
            "Waarde ($)": item.get("amount", "Onbekend")
        }
        records.append(record)
        tickers.add(ticker)

    df = pd.DataFrame(records)
    return df, list(tickers)

def enrich_prices(df, tickers):
    current_prices = {}
    for ticker in tickers:
        try:
            hist = yf.download(ticker, period="90d", interval="1d", progress=False)
            current_price = yf.Ticker(ticker).info["regularMarketPrice"]
            current_prices[ticker] = current_price
        except:
            continue

        for i, row in df[df["Aandeel"] == ticker].iterrows():
            try:
                tx_date = row["RawDatum"]
                if tx_date not in hist.index:
                    tx_date = hist.index[hist.index.get_loc(tx_date, method='nearest')]
                price = hist.loc[tx_date]["Close"]
                df.at[i, "Aankoopprijs ($)"] = round(price, 2)
                df.at[i, "Huidige prijs ($)"] = round(current_prices.get(ticker, 0), 2)

                if price and current_prices.get(ticker):
                    rendement = ((current_prices[ticker] - price) / price) * 100
                    df.at[i, "Rendement (%)"] = round(rendement, 2)
            except:
                continue

    return df, current_prices

# ---------- STREAMLIT FRONTEND ----------
st.set_page_config(page_title="Politiek Aandelen Dashboard")
st.markdown("# 🇺🇸 Politiek Aandelen Dashboard")
st.markdown("Geselecteerde transacties van prominente Amerikaanse politici.")

df, tickers = load_data()
df, live_prices = enrich_prices(df, tickers)
df.fillna("-", inplace=True)

politici = df["Politicus"].unique()
selectie = st.multiselect("Kies politicus:", options=politici, default=politici[:4])
filtered = df[df["Politicus"].isin(selectie)]

# ✅ Laatste transactie tonen
if not df.empty:
    laatste = df.sort_values(by="RawDatum", ascending=False).iloc[0]
    st.markdown(f"📌 **Laatste transactie:** {laatste['Datum']} door {laatste['Politicus']} ({laatste['Aandeel']})")

# ✅ Actuele koersen
timestamp = datetime.utcnow().strftime("%d-%m-%Y %H:%M UTC")
st.markdown(f"📉 **Actuele koersen** _(laatst bijgewerkt: {timestamp})_")
for t in selectie:
    tickers = df[df["Politicus"] == t]["Aandeel"].unique()
    for share in tickers:
        prijs = live_prices.get(share)
        if prijs:
            st.markdown(f"- **{share}**: ${prijs}")
        else:
            st.markdown(f"- **{share}**: *(niet beschikbaar)*")

# 📊 Tabel
st.markdown("📊 **Geselecteerde transacties**")
kolommen = [
    "Politicus", "Aandeel", "Datum", "Transactie", "Waarde ($)",
    "Aankoopprijs ($)", "Huidige prijs ($)", "Rendement (%)"
]
st.dataframe(filtered[kolommen], use_container_width=True)

# 📥 Download
st.download_button(
    "📩 Download als Excel",
    data=filtered[kolommen].to_csv(index=False).encode(),
    file_name="transacties.csv",
    mime="text/csv"
)
