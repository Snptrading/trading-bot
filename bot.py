import pandas as pd
import yfinance as yf
import requests
import os

# -----------------------------
# TELEGRAM SETUP
# -----------------------------
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ Telegram credentials missing!")
        return

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
def run_strategy():
    try:
        # Reduced data size → faster + safer
        data = yf.download("^GDAXI", period="2y", interval="1h")

        if data.empty:
            print("No data received!")
            return None

        # Fix multi-index if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna()

        # Bollinger Bands
        window = 30
        data["Mean"] = data["Close"].rolling(window).mean()
        data["Std"] = data["Close"].rolling(window).std()

        data["Lower"] = data["Mean"] - 1.5 * data["Std"]
        data["Upper"] = data["Mean"] + 1.5 * data["Std"]

        # Optional trend filter (reduces false signals)
  #      data["Trend"] = data["Close"].rolling(100).mean()

        # Signals
        data["Signal"] = 0
        data.loc[data["Close"] < data["Lower"], "Signal"] = 1
        data.loc[data["Close"] > data["Upper"], "Signal"] = -1

        return data

    except Exception as e:
        print("Error in strategy:", e)
        return None


# -----------------------------
# MAIN EXECUTION
# -----------------------------
def main():
    data = run_strategy()

    if data is None:
        print("❌ No data → exiting")
        return

    # Last signal
    last_signal = int(data["Signal"].iloc[-1])
    last_price = float(data["Close"].iloc[-1])
    last_date = data.index[-1]

    print(f"LAST: {last_date} | Price: {last_price:.2f} | Signal: {last_signal}")

    # -----------------------------
    # PRINT LAST 48 HOURS
    # -----------------------------
    try:
        last_48h = data.loc[
            data.index >= (data.index.max() - pd.Timedelta(hours=48))
        ].copy()

        # Safe timezone handling
        if last_48h.index.tz is not None:
            last_48h.index = last_48h.index.tz_convert(None)

        last_48h = last_48h.round(2)

        print("\n===== LAST 48 HOURS =====")
        print(last_48h[["Close", "Mean", "Upper", "Lower", "Signal"]])

    except Exception as e:
        print("Error printing last 48h:", e)
# -----------------------------
# TEST TELEGRAM
# -----------------------------
send_telegram("✅ Bot started successfully")
    # -----------------------------
    # SEND TELEGRAM SIGNAL
    # -----------------------------
    if last_signal == 1:
        msg = f"{last_date}\n🟢 BUY\nPrice: {last_price:.2f}"
        send_telegram(msg)
        print("BUY SENT")

    elif last_signal == -1:
        msg = f"{last_date}\n🔴 SELL\nPrice: {last_price:.2f}"
        send_telegram(msg)
        print("SELL SENT")

    else:
        print("No signal → nothing sent")


# -----------------------------
# RUN SCRIPT
# -----------------------------
if __name__ == "__main__":
    print("🚀 Bot started")
    main()
