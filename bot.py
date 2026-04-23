import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import time
import requests

# -----------------------------
# TELEGRAM SETUP
# -----------------------------
TOKEN = "8616334658:AAHn0BO4EhLLRiUfGVAqtSs1zolch8qIs80"
CHAT_ID = 8465330966

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        if r.status_code != 200:
            print("Telegram error:", r.text)
    except Exception as e:
        print("Telegram exception:", e)

# -----------------------------
# STRATEGY FUNCTION
# -----------------------------
def run_strategy():
    data = yf.download("NQ=F", period="1y", interval="1d")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.dropna()

    # -----------------------------
    # Bollinger Bands
    # -----------------------------
    window = 20
    data["Mean"] = data["Close"].rolling(window).mean()
    data["Std"] = data["Close"].rolling(window).std()

    data["Lower"] = data["Mean"] - 1.2 * data["Std"]
    data["Upper"] = data["Mean"] + 1.2 * data["Std"]

    # -----------------------------
    # Signals
    # -----------------------------
    data["Signal"] = 0
    data.loc[data["Close"] < data["Lower"], "Signal"] = 1
    data.loc[data["Close"] > data["Upper"], "Signal"] = -1

    data["Action"] = "HOLD"
    data.loc[data["Signal"] == 1, "Action"] = "BUY"
    data.loc[data["Signal"] == -1, "Action"] = "SELL"

    return data


# -----------------------------
# INITIAL RUN
# -----------------------------
data = run_strategy()

print("\n===== TRADE LIST =====")
print(data[data["Action"] != "HOLD"][["Close", "Action"]].tail(20))

print("\n===== LAST 15 DAYS =====")
print(data[["Close", "Lower", "Mean", "Upper", "Signal", "Action"]].tail(15))

# -----------------------------
# PLOT
# -----------------------------
buy = data[data["Signal"] == 1]
sell = data[data["Signal"] == -1]

cutoff_date = data.index.max() - pd.Timedelta(days=90)
recent = data.loc[data.index >= cutoff_date]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12,10))

ax1.plot(data["Close"], label="Price")
ax1.plot(data["Mean"], label="Mean")
ax1.plot(data["Upper"], "--", label="Upper")
ax1.plot(data["Lower"], "--", label="Lower")

ax1.scatter(buy.index, buy["Close"], marker="^", color="green", label="BUY", s=80)
ax1.scatter(sell.index, sell["Close"], marker="v", color="red", label="SELL", s=80)
ax1.set_title("Full Data")
ax1.legend()

ax2.plot(recent["Close"], label="Price")
ax2.plot(recent["Mean"], label="Mean")
ax2.plot(recent["Upper"], "--", label="Upper")
ax2.plot(recent["Lower"], "--", label="Lower")

ax2.scatter(recent[recent["Signal"] == 1].index,
            recent[recent["Signal"] == 1]["Close"],
            marker="^", color="green", s=80, label="BUY")

ax2.scatter(recent[recent["Signal"] == -1].index,
            recent[recent["Signal"] == -1]["Close"],
            marker="v", color="red", s=80, label="SELL")

ax2.set_title("Last 3 Months")
ax2.legend()

plt.tight_layout()
plt.show()

# -----------------------------
# REAL-TIME MONITORING
# -----------------------------
print("\nMonitoring started...\n")

previous_signal = None   # FIXED

while True:

    time.sleep(86400)  # 24 hours (correct for daily data)

    data = run_strategy()

    last_signal = data["Signal"].iloc[-1]
    last_date = data.index[-1]

    # ignore first run
    if previous_signal is None:
        previous_signal = last_signal
        continue

    if last_signal != previous_signal:

        if last_signal == 1:
            msg = f"🟢 BUY signal on {last_date.date()}"
            send_telegram(msg)
            print(msg)

        elif last_signal == -1:
            msg = f"🔴 SELL signal on {last_date.date()}"
            send_telegram(msg)
            print(msg)

        else:
            print(f"⚪ HOLD on {last_date.date()}")

        previous_signal = last_signal
