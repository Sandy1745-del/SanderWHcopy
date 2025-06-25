import streamlit as st
import pandas as pd

st.set_page_config(page_title="Capitol Trades Dashboard", layout="wide")
st.title("🏛️ Capitol Trades Dashboard")
st.caption("Recente aandelentransacties van prominente Amerikaanse politici")

@st.cache_data(ttl=3600)
def load_data():
    url = "https://www.capitoltrades.com/trades"
    tables = pd.read_html(url)
    return tables[0] if tables else pd.DataFrame()

try:
    df = load_data()
    if not df.empty:
        st.success("✅ Data succesvol opgehaald van CapitolTrades.com!")

        # Format kolommen
        def format_politician(raw):
            name = raw.replace("Democrat", "**Democrat**").replace("Republican", "**Republican**")
            name = name.replace("Senate", " Senate").replace("House", " House")
            return f"<b>{name.split('**')[0]}</b><br>{'**'.join(name.split('**')[1:])}"

        df["Politician"] = df["Politician"].astype(str).apply(format_politician)
        df["Published"] = df["Published"].str.replace("Yesterday", " Yesterday")
        df["Filed After"] = df["Filed After"].str.replace("days", "days ")
        
        if "Unnamed: 9" in df.columns:
            df["🔗 Trade Link"] = df["Unnamed: 9"].apply(
                lambda x: f'<a href="https://www.capitoltrades.com{x.split(" ")[-1]}" target="_blank">Details</a>' 
                if isinstance(x, str) and "Goto" in x else "")
            df.drop(columns=["Unnamed: 9"], inplace=True)

        # Selecteer relevante kolommen
        display_df = df[["Politician", "Traded Issuer", "Published", "Traded", 
                         "Filed After", "Owner", "Type", "Size", "Price", "🔗 Trade Link"]]

        # Converteer naar HTML
        html_table = display_df.to_html(escape=False, index=False)
        st.markdown(html_table, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Geen data beschikbaar.")
except Exception as e:
    st.error(f"❌ Fout bij ophalen van data: {e}")
