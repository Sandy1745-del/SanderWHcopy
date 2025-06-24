import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime
import pytz

st.set_page_config(page_title="Politiek Aandelen Dashboard", layout="wide")

# ─── DATAFUNCTIES ───────────────────────────────────────────────────────────────

@st.cache_data
def fetch_trades():
    try:
        url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            st.warning("⚠️ Fout bij ophalen van data. Probeer het later opnieuw.")
            return pd.DataFrame()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Fout bij verbinding met API: {e}")
        return pd.DataFrame()

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

# ─── VOORBEREIDING ───────────────────────────────────────────────────────────────

df = fetch_trades()

if df.empty or "representative" not in df.columns:
    st.warning("⚠️ Geen geldige data gevonden. Mogelijk is de bron tijdelijk onbereikbaar.")
    st.stop()

df = df[df["transaction_date"].notna()]
df = df[df["asset_description"].notna()]
df = df[~df["asset_description"].str.contains(" ")]
df = df[df["asset_description"].str.len() <= 5]

df["Datum"] = pd.to_datetime(df["transaction_date"]).dt.strftime("%d-%m-%Y")
df["Aandeel"] = df["asset_description"].str.upper()
df["Politicus"] = df["representative"]
df["Transactie"] = df["type"]
df["Waarde ($)"] = df["amount"]

# ─── KOERS + RENDEMENT ──────────────────────────────────────────────────────────

tickers = df["Aandeel"].unique().tolist()
koersen = get_current_prices(tickers)

df["Aankoopprijs"] = "-"
df["Actuele prijs"] = "-"
df["Rendement (%)"] = "-"

for i, row in df.iterrows():
    ticker = row["Aandeel"]
    try:
        hist = yf.download(ticker, period="6mo", progress=False)
        tx_date = pd.to_datetime(row["transaction_date"])
        tx_date = hist.index[hist.index.get_indexer([tx_date], method='nearest')[0]]
        aankoop = hist.loc[tx_date]["Close"]
        actueel = koersen.get(ticker, None)
        if actueel:
            rendement = ((actueel - aankoop) / aankoop) * 100
            df.at[i, "Aankoopprijs"] = round(aankoop, 2)
            df.at[i, "Actuele prijs"] = round(actueel, 2)
            df.at[i, "Rendement (%)"] = round(rendement, 2)
    except:
        continue

# ─── STREAMLIT UI ────────────────────────────────────────────────────────────────

st.title("🇺🇸 Politiek Aandelen Dashboard")
st.markdown("Geselecteerde transacties van prominente Amerikaanse politici.")

if df.empty or "Politicus" not in df.columns:
    st.warning("⚠️ Geen data beschikbaar.")
    st.stop()

politici = df["Politicus"].unique()
selectie = st.multiselect("Kies politicus:", sorted(politici), default=politici[:4])

filtered = df[df["Politicus"].isin(selectie)].copy()

# ─── KOERS OVERZICHT ─────────────────────────────────────────────────────────────

if not filtered.empty:
    st.markdown("📉 **Actuele koersen** _(in EUR, laatst bijgewerkt: {} Amsterdamse tijd)_".format(
        datetime.now(pytz.timezone("Europe/Amsterdam")).strftime("%d-%m-%Y %H:%M")
    ))

    for ticker in sorted(set(filtered["Aandeel"])):
        prijs = koersen.get(ticker)
        if prijs:
            st.markdown(f"- **{ticker}**: ${prijs}")

# ─── TABEL MET KLEURCODE ────────────────────────────────────────────────────────

def kleur_rendement(val):
    try:
        if float(val) > 0:
            return "color: green;"
        elif float(val) < 0:
            return "color: red;"
    except:
        return ""
    return ""

st.markdown("📊 **Geselecteerde transacties**")

kolommen = [
    "Politicus", "Aandeel", "Datum", "Transactie", "Waarde ($)",
    "Aankoopprijs", "Actuele prijs", "Rendement (%)"
]

styled_df = filtered[kolommen].style.applymap(kleur_rendement, subset=["Rendement (%)"])
st.dataframe(styled_df, use_container_width=True)

# ─── DOWNLOAD ────────────────────────────────────────────────────────────────────

csv = filtered[kolommen].to_csv(index=False).encode("utf-8")
st.download_button("📩 Download als Excel", csv, "transacties.csv", "text/csv")
