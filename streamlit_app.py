import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz

# Zet pagina-configuratie
st.set_page_config(page_title="Capitol Trades Dashboard", layout="wide")

st.markdown("## 🏛️ Capitol Trades Dashboard")
st.markdown("Bekijk recente aandelenaankopen en -verkopen van Amerikaanse politici.")

# Laad data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("sample_data.csv")
        df["Datum"] = pd.to_datetime(df["Datum"]).dt.strftime("%d-%m-%Y")
        df["Transactie"] = df["Transactie"].replace({
            "purchase": "Aankoop",
            "sell_partial": "Verkoop",
            "sell_full": "Verkoop"
        })
        return df
    except:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ Geen data beschikbaar.")
    st.stop()
else:
    st.success("✅ Dataframe succesvol geladen!")

# Haal tickers en huidige prijzen op
@st.cache_data(ttl=3600)
def get_live_prices(tickers):
    prices = {}
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period="1d")
            prices[ticker] = round(data["Close"].iloc[-1], 2)
        except:
            prices[ticker] = None
    return prices

tickers = df["Aandeel"].unique().tolist()
live_prices = get_live_prices(tickers)

# Toon timestamp van update
amsterdam = pytz.timezone("Europe/Amsterdam")
now_ams = datetime.now(amsterdam).strftime("%d-%m-%Y %H:%M")
st.markdown(f"📈 Actuele koersen (USD) – _laatst bijgewerkt: {now_ams}_")

for ticker in tickers:
    prijs = live_prices.get(ticker)
    if prijs:
        st.markdown(f"- **{ticker}**: ${prijs}")
    else:
        st.markdown(f"- **{ticker}**: niet beschikbaar")

# Voeg aankoopprijs + rendement toe
def calculate_returns(df, live_prices):
    df["Aankoopprijs"] = None
    df["Huidige prijs ($)"] = None
    df["Rendement (%)"] = None

    for i, row in df.iterrows():
        try:
            ticker = row["Aandeel"]
            date = datetime.strptime(row["Datum"], "%d-%m-%Y")
            price_data = yf.Ticker(ticker).history(start=date, end=date + pd.Timedelta(days=2))
            price_on_date = price_data["Close"].iloc[0]
            current_price = live_prices.get(ticker, None)

            if isinstance(current_price, (int, float)) and price_on_date:
                rendement = ((current_price - price_on_date) / price_on_date) * 100
                df.at[i, "Aankoopprijs"] = round(price_on_date, 2)
                df.at[i, "Huidige prijs ($)"] = current_price
                df.at[i, "Rendement (%)"] = round(rendement, 2)
        except:
            continue
    return df

df = calculate_returns(df, live_prices)

# Filter op datum > 01-01-2025
df["Datum_dt"] = pd.to_datetime(df["Datum"], format="%d-%m-%Y")
df = df[df["Datum_dt"] >= pd.Timestamp("2025-01-01")]
df = df.sort_values(by="Datum_dt", ascending=False)

# Politici filter
politici = df["Politicus"].unique().tolist()
selected_politici = st.multiselect("Kies politicus:", options=politici, default=politici)

filtered_df = df[df["Politicus"].isin(selected_politici)]

# Toon tabel
st.markdown("### 📉 Geselecteerde transacties")

if filtered_df.empty:
    st.warning("⚠️ Geen resultaten voor deze selectie.")
else:
    show_df = filtered_df[[
        "Politicus", "Aandeel", "Datum", "Transactie", "Waarde ($)",
        "Aankoopprijs", "Huidige prijs ($)", "Rendement (%)"
    ]]

    def kleur_rendement(val):
        if isinstance(val, (int, float)):
            color = "green" if val > 0 else "red"
            return f"color: {color}"
        return ""

    st.dataframe(show_df.style.applymap(kleur_rendement, subset=["Rendement (%)"]), use_container_width=True)

    # Download knop
    st.download_button("📥 Download als CSV", data=show_df.to_csv(index=False).encode("utf-8"), file_name="gefilterde_transacties.csv")
