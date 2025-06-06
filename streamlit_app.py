import streamlit as st
import pandas as pd

st.title("Politiek Aandelen Dashboard")

@st.cache_data
def load_data():
    df = pd.read_csv("sample_data.csv")
    return df

df = load_data()

politici = st.multiselect("Kies politicus:", options=df["Politicus"].unique(), default=df["Politicus"].unique())
df_filtered = df[df["Politicus"].isin(politici)]

st.write("📊 Geselecteerde transacties")
st.dataframe(df_filtered)

st.download_button("📥 Download als Excel", df_filtered.to_csv(index=False), file_name="politieke_transacties.csv")
