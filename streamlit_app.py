import streamlit as st
import pandas as pd

st.set_page_config(page_title="Capitol Trades Dashboard", page_icon="🏛️")

st.title("🏛️ Capitol Trades Dashboard")
st.markdown("Bekijk recente aandelenaankopen en -verkopen van Amerikaanse politici.")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("sample_data.csv")
        st.write("✅ Dataframe succesvol geladen!")
        st.write(df.head())  # Laat eerste rijen zien
        st.write("🔍 Kolommen:", df.columns.tolist())

        # Zorg dat datum kolom goed is
        df["Datum"] = pd.to_datetime(df["Datum"], errors='coerce')

        # Debug: toon unieke datums
        st.write("📅 Unieke datums in dataset:", df["Datum"].dt.date.unique())

        # Filter op recente transacties vanaf 2025
        df = df[df["Datum"] >= pd.to_datetime("2025-01-01")]

        # Debug: controle na filtering
        st.write("📊 Data na filtering:")
        st.write(df.head())

        return df
    except Exception as e:
        st.error(f"❌ Fout bij inladen data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ Geen data beschikbaar na filtering of inleesfout.")
    st.stop()

# Politici lijst voor dropdown
politici = df["Politicus"].unique()
selectie = st.multiselect("Kies politicus:", politici, default=politici.tolist())

# Filter op geselecteerde politici
filtered_df = df[df["Politicus"].isin(selectie)]

if filtered_df.empty:
    st.warning("⚠️ Geen resultaten voor geselecteerde politici.")
else:
    st.subheader("📈 Geselecteerde transacties")
    st.dataframe(filtered_df)

    # Downloadknop
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download als CSV", data=csv, file_name="geselecteerde_transacties.csv", mime="text/csv")
