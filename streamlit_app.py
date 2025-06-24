import streamlit as st
import pandas as pd

# Laad dataset vanaf GitHub
csv_url = "https://raw.githubusercontent.com/Sandy1745-del/SanderWHcopy/main/sample_data.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(csv_url)
    return df

df = load_data()

st.title("🇺🇸 Politiek Aandelen Dashboard")
st.markdown("Geselecteerde transacties van prominente Amerikaanse politici.")

politici = df["Politicus"].unique().tolist()
selectie = st.multiselect("Kies politicus:", opties := politici, default=politici)

filtered = df[df["Politicus"].isin(selectie)]
st.write("📊 Geselecteerde transacties")
st.dataframe(filtered)

st.download_button("📥 Download als Excel", filtered.to_csv(index=False), file_name="politiek_aandelen.csv")
