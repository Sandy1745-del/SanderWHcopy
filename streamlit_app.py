import streamlit as st
import pandas as pd

st.set_page_config(page_title="Capitol Trades Dashboard", layout="wide")
st.title("🏛️ Capitol Trades Dashboard")
st.write("Recente aandelentransacties van prominente Amerikaanse politici")

@st.cache_data(ttl=3600)
def load_data():
    url = "https://www.capitoltrades.com/trades"
    tables = pd.read_html(url)
    return tables[0] if tables else pd.DataFrame()

try:
    df = load_data()
    if not df.empty:
        st.success("✅ Data succesvol opgehaald van CapitolTrades.com!")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ Geen data beschikbaar.")
except Exception as e:
    st.error(f"❌ Fout bij ophalen van data: {e}")
