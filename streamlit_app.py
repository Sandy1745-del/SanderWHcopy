import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta

def fetch_political_trades():
    url = "https://housestockwatcher.com/api/financial-disclosures"
    response = requests.get(url)
    data = response.json()
    return data

def process_data(trades):
    records = []
    tickers = set()

    for item in trades:
        if not item.get("assetDescription") or not item.get("transactionDate"):
            continue

        ticker = item["assetDescription"].strip().upper()
        if len(ticker) > 6 or " " in ticker:
            continue

        try:
            date = datetime.strptime(item["transactionDate"], "%Y-%m-%d")
        except:
            continue

        record = {
            "Politicus": item.get("representative", "Onbekend"),
            "Aandeel": ticker,
            "Datum": date.strftime("%Y-%m-%d"),
            "Transactie": item.get("type", "Onbekend"),
            "Waarde ($)": item.get("amount", "Onbekend"),
        }
        records.append(record)
        tickers.add(ticker)

    return records, list(tickers)

def add_price_changes(df, tickers):
    one_day = timedelta(days=1)
    one_week = timedelta(weeks=1)
    one_month = timedelta(days=30)

    for ticker in tickers:
        try:
            hist = yf.download(ticker, period="60d", interval="1d", progress=False)
        except:
            continue

        for i, row in df[df["Aandeel"] == ticker].iterrows():
            try:
                tx_date = datetime.strptime(row["Datum"], "%Y-%m-%d")
                if tx_date not in hist.index:
                    tx_date = hist.index[hist.index.get_loc(tx_date, method='nearest')]

                price = hist.loc[tx_date]["Close"]

                d1 = tx_date + one_day
                d7 = tx_date + one_week
                d30 = tx_date + one_month

                for label, target_date in zip(["Koers +1d (%)", "Koers +1w (%)", "Koers +1m (%)"], [d1, d7, d30]):
                    if target_date in hist.index:
                        future_price = hist.loc[target_date]["Close"]
                        change = ((future_price - price) / price) * 100
                        df.at[i, label] = round(change, 2)
            except:
                continue

    return df

def main():
    trades = fetch_political_trades()
    records, tickers = process_data(trades)
    df = pd.DataFrame(records)
    df = add_price_changes(df, tickers)
    df["Koers +1d (%)"] = df["Koers +1d (%)"].fillna("-")
    df["Koers +1w (%)"] = df["Koers +1w (%)"].fillna("-")
    df["Koers +1m (%)"] = df["Koers +1m (%)"].fillna("-")

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    df.to_csv("sample_data.csv", index=False)

    with open("UPDATE_LOG.md", "w") as f:
        f.write(f"Laatst bijgewerkt op: {timestamp}\nAantal records: {len(df)}")

if __name__ == "__main__":
    main()
