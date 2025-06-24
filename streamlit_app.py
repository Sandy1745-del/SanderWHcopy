import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from datetime import datetime
import pytz
import os

st.set_page_config(page_title="Politiek Aandelen Dashboard", layout="wide")

def fetch_disclosure_zip(year=2025):
    zip_url = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
    try:
        response = requests.get(zip_url, timeout=20)
        response.raise_for_status()
    except Exception as e:
        return None, f"❌ Download fout voor {year}FD.zip: {e}"

    try:
        zip_file = zipfile.ZipFile(BytesIO(response.content))
        xml_files = [f for f in zip_file.namelist() if f.endswith(".xml")]
    except:
        return None, "❌ ZIP-bestand kan niet worden uitgepakt of bevat geen XML-bestanden."

    records = []
    for xml_name in xml_files:
        with zip_file.open(xml_name) as f:
            try:
                tree = ET.parse(f)
                root = tree.getroot()

                filer_info = root.find(".//FilerInfo")
                name_parts = []
                if filer_info is not None:
                    for tag in ["First", "Middle", "Last"]:
                        value = filer_info.find(tag)
                        if value is not None and value.text:
                            name_parts.append(value.text.strip())
                representative = " ".join(name_parts)

                assets = root.findall(".//Asset")
                for asset in assets:
                    asset_name = asset.findtext("Name", default="").strip()
                    trans_type = asset.findtext("TransactionType", default="").strip()
                    trans_date = asset.findtext("TransactionDate", default="").strip()
                    amount = asset.findtext("Amount", default="").strip()

                    if not (asset_name and trans_type and trans_date):
                        continue

                    try:
                        parsed_date = datetime.strptime(trans_date, "%m/%d/%Y")
                        if parsed_date.year < year:
                            continue
                        trans_date = parsed_date.strftime("%Y-%m-%d")
                    except:
                        continue

                    records.append({
                        "representative": representative,
                        "asset_description": asset_name.upper(),
                        "transaction_date": trans_date,
                        "type": trans_type.lower(),
                        "amount": amount
                    })
            except:
                continue

    df = pd.DataFrame(records)
    if not df.empty:
        df.to_csv("sample_data.csv", index=False)
        return df, f"📥 Gegevens geladen uit officiële {year} ZIP (House Disclosure)"
    else:
        return None, "⚠️ Geen bruikbare data gevonden in ZIP"

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

df, status = fetch_disclosure_zip()
if df is None or df.empty:
    try:
        df = pd.read_csv("sample_data.csv", parse_dates=["transaction_date"])
        status = "⚠️ ZIP-download mislukt – sample gebruikt"
    except:
        st.error("❌ Geen data beschikbaar.")
        st.stop()

df = df[df["transaction_date"].notna()]
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

st.title("🇺🇸 Politiek Aandelen Dashboard")
st.markdown(status)

politici = df["Politicus"].unique()
selectie = st.multiselect("Kies politicus:", sorted(politici), default=politici[:5])
filtered = df[df["Politicus"].isin(selectie)].copy()

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
