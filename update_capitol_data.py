import requests
import pandas as pd
from datetime import datetime
import os

def fetch_data():
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise ValueError("APIFY_TOKEN ontbreekt")

    url = "https://api.apify.com/v2/actor-tasks/mYqen3NsZ1hW2mJd8/run-sync-get-dataset-items?token=" + token
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def process_data(items):
    df = pd.DataFrame(items)
    df = df[["politician", "ticker", "transaction_date", "amount", "type"]]
    df.columns = ["Politicus", "Aandeel", "Datum", "Waarde ($)", "Transactie"]
    df["Datum"] = pd.to_datetime(df["Datum"]).dt.strftime("%Y-%m-%d")
    df.to_csv("sample_data.csv", index=False)

if __name__ == "__main__":
    items = fetch_data()
    process_data(items)
