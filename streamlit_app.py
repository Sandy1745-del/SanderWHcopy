import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
import pytz

def get_closest_price(ticker, date):
    try:
        hist = yf.download(ticker, start=date - timedelta(days=5), end=date + timedelta(days=5), interval="1d", progress=False)
        if not hist.empty:
            closest_idx = hist.index.get_loc(date, method='nearest')
            return hist.iloc[closest_idx]['Close']
    except:
        return None

def process_dataframe(file_path):
    df = pd.read_csv(file_path)
    df["Datum"] = pd.to_datetime(df["Datum"])
    df = df[df["Datum"] >= datetime(2025, 1, 1)]
    df = df.sort_values(by="Datum", ascending=False)
    df["Datum"] = df["Datum"].dt.strftime("%d-%m-%Y")

    koersen = {}
    for ticker in df["Aandeel"].unique():
        try:
            data = yf.Ticker(ticker).history(period="1d")
            if not data.empty:
                koersen[ticker] = data["Close"].iloc[-1]
        except:
            koersen[ticker] = None

    df["Aankoopprijs"] = None
    df["Huidige prijs ($)"] = None
    df["Rendement (%)"] = None

    for i, row in df.iterrows():
        try:
            aankoop_datum = datetime.strptime(row["Datum"], "%d-%m-%Y")
            aandeel = row["Aandeel"]
            aankoopprijs = get_closest_price(aandeel, aankoop_datum)
            df.at[i, "Aankoopprijs"] = aankoopprijs

            huidige_koers = koersen.get(aandeel)
            df.at[i, "Huidige prijs ($)"] = huidige_koers

            if aankoopprijs and huidige_koers:
                rendement = ((huidige_koers - aankoopprijs) / aankoopprijs) * 100
                df.at[i, "Rendement (%)"] = round(rendement, 2)
        except:
            continue

    df["Transactie"] = df["Transactie"].replace({
        "purchase": "Aankoop",
        "sell_full": "Verkoop"
    })

    return df, koersen

# Streamlit UI
st.set_page_config("Capitol Trades Dashboard", page_icon="🏛️", layout="wide")
st.title("🏛️ Capitol Trades Dashboard")
st.write("Bekijk recente aandelenaankopen en -verkopen van Amerikaanse politici.")

try:
    df, koersen = process_dataframe("sample_data.csv")
    st.success("✅ Dataframe succesvol geladen!")

    ams_now = datetime.now(pytz.timezone("Europe/Amsterdam"))
    tijd = ams_now.strftime("%d-%m-%Y %H:%M")

    st.markdown(f"### 🧾 Actuele koersen (USD) – _laatst bijgewerkt: {tijd}_")
    for ticker, prijs in koersen.items():
        if prijs:
            st.markdown(f"- [{ticker}](https://finance.yahoo.com/quote/{ticker}) : **${round(prijs, 2)}**", unsafe_allow_html=True)

    politici = df["Politicus"].unique().tolist()
    selectie = st.multiselect("Kies politicus:", politici, default=politici)

    gefilterd = df[df["Politicus"].isin(selectie)]

    if not gefilterd.empty:
        st.markdown("### 📉 Geselecteerde transacties")
        def kleur(x):
            if isinstance(x, float):
                return f"color: {'green' if x > 0 else 'red'}"
            return ""
        st.dataframe(gefilterd.style.applymap(kleur, subset=["Rendement (%)"]), use_container_width=True)

        csv = gefilterd.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download als CSV", csv, "transacties.csv", "text/csv")
    else:
        st.warning("⚠️ Geen data beschikbaar.")
except Exception as e:
    st.error(f"❌ Fout bij laden van data: {e}")
