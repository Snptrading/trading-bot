import pandas as pd
import yfinance as yf
import time
import requests
import matplotlib.pyplot as plt
import os

# -----------------------------
# TELEGRAM SETUP
# -----------------------------
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

        print("Telegram status:", r.status_code)

        if r.status_code != 200:
            print("Telegram error:", r.text)

    except Exception as e:
        print("Telegram exception:", e)


# -----------------------------
# STRATEGY FUNCTION
# -----------------------------
# Rheinmetall AG (RHM.DE), Nasdaq (NQ=F), S&P 500 (^GSPC), Gold (GC=F), Germanz DAX (^GDAXI),
def run_strategy():
    data = yf.download("^GDAXI", period="2y", interval="1h")

    if data.empty:
        print("No data received!")
        return None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.dropna()

    # Bollinger Bands
    window = 30
    data["Mean"] = data["Close"].rolling(window).mean()
    data["Std"] = data["Close"].rolling(window).std()

    data["Lower"] = data["Mean"] - 1.5 * data["Std"]
    data["Upper"] = data["Mean"] + 1.5 * data["Std"]

    # Signals
    data["Signal"] = 0
    data.loc[data["Close"] < data["Lower"], "Signal"] = 1
    data.loc[data["Close"] > data["Upper"], "Signal"] = -1

    return data

data = run_strategy()

last_24h = data.loc[
    data.index >= (data.index.max() - pd.Timedelta(hours=48))
]
last_24h = last_24h.copy()
last_24h.index = last_24h.index.tz_convert(None)
last_24h = last_24h.round(2)
# -----------------------------
# list of last 24 h data with signal
# -----------------------------
print("\n===== LAST 24 HOURS =====")
print(last_24h[["Close", "Mean", "Upper", "Lower", "Signal"]])
# -----------------------------
# INITIAL PLOT (RUN ONCE)
# -----------------------------
data = run_strategy()

if data is not None:

    buy = data[data["Signal"] == 1]
    sell = data[data["Signal"] == -1]

    cutoff_date = data.index.max() - pd.Timedelta(days=90)
    recent = data.loc[data.index >= cutoff_date]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    ax1.plot(data["Close"], label="Price")
    ax1.plot(data["Mean"], label="Mean")
    ax1.plot(data["Upper"], "--", label="Upper")
    ax1.plot(data["Lower"], "--", label="Lower")

    ax1.scatter(buy.index, buy["Close"], marker="^", color="green", s=80, label="BUY")
    ax1.scatter(sell.index, sell["Close"], marker="v", color="red", s=80, label="SELL")

    ax1.set_title("Full Data")
    ax1.legend()
    ax1.grid(True)

    ax2.plot(recent["Close"], label="Price")
    ax2.plot(recent["Mean"], label="Mean")
    ax2.plot(recent["Upper"], "--", label="Upper")
    ax2.plot(recent["Lower"], "--", label="Lower")

    ax2.scatter(recent[recent["Signal"] == 1].index,
                recent[recent["Signal"] == 1]["Close"],
                marker="^", color="green", s=80)

    ax2.scatter(recent[recent["Signal"] == -1].index,
                recent[recent["Signal"] == -1]["Close"],
                marker="v", color="red", s=80)

    ax2.set_title("Last 2.5 Months")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
#    plt.show()   # ✅ BLOCKING → ensures proper rendering


# -----------------------------
# TEST TELEGRAM
# -----------------------------
send_telegram("✅ Bot started successfully")


# -----------------------------
# REAL-TIME MONITORING
# -----------------------------
print("\nMonitoring started...\n")

previous_signal = None

def check_signal():
    data = run_strategy()

    if data is None:
        return

    last_signal = int(data["Signal"].iloc[-1])
    last_price = float(data["Close"].iloc[-1])
    last_date = data.index[-1]

    msg = f"{last_date}\nSignal: {last_signal}\nPrice: {last_price:.2f}"
    send_telegram(msg)

check_signal()
