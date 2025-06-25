import streamlit as st
import pandas as pd
import requests

# Config
st.set_page_config(page_title="Capitol Trades Dashboard", layout="wide")
st.title("\U0001F3DB️ Capitol Trades Dashboard")
st.caption("Recente aandelentransacties van prominente Amerikaanse politici")

# URL van de pagina met transacties
url = "https://www.capitoltrades.com/trades"

# Data proberen in te laden
try:
    dfs = pd.read_html(url)
    df = dfs[0]
    st.success("✅ Data succesvol opgehaald van CapitolTrades.com!")

    # Kolom: Politician => formatteer naar naam + partij/positie
    def format_politician(row):
        name = row.split("Democrat") if "Democrat" in row else row.split("Republican")
        party_info = "Democrat" + name[1] if len(name) > 1 and "Democrat" in row else ("Republican" + name[1] if len(name) > 1 else "")
        return f"**{name[0].strip()}**\n{party_info.replace('Senate', ' Senate').replace('House', ' House')}"

    df["Politician"] = df["Politician"].astype(str).apply(format_politician)

    # Fix spacing in Published (tijd en 'Yesterday')
    df["Published"] = df["Published"].str.replace("Yesterday", " Yesterday")

    # Spatie tussen 'days' en getal in 'Filed After'
    df["Filed After"] = df["Filed After"].str.replace(r"days(\d+)", r"days \1", regex=True)

    # Maak van 'Goto trade detail page' een echte link
    if "Unnamed: 9" in df.columns:
        df["Link"] = df["Unnamed: 9"].apply(lambda x: f'[Details](https://www.capitoltrades.com{x.split(" ")[-1]})' if isinstance(x, str) and "Goto" in x else "")
        df.drop(columns=["Unnamed: 9"], inplace=True)

    # Kolomnamen netter maken
    df.rename(columns={
        "Politician": "🧑 Politician",
        "Traded Issuer": "🏢 Traded Issuer",
        "Published": "🕒 Published",
        "Traded": "📅 Traded",
        "Filed After": "📁 Filed After",
        "Owner": "👤 Owner",
        "Type": "📈 Type",
        "Size": "💰 Size",
        "Price": "💵 Price",
        "Link": "🔗 Trade Link"
    }, inplace=True)

    # Toon tabel
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ Fout bij ophalen van data: {e}")
