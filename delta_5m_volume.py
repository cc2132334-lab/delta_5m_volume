import time
from datetime import datetime
import pytz
import requests

# --- TELEGRAM CONFIG ---
BOT_TOKEN = "8626042409:AAHElsiJD8_Jk9R7r5VHUj8fPjcl8Meacp4"
CHAT_ID = "706694019"

# Symbols
SYMBOLS = ["BTCUSD", "ETHUSD"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_delta_5m_candles(symbol, count=40):
    end_time = int(time.time())
    start_time = end_time - (count * 5 * 60)
        
    url = "https://api.india.delta.exchange/v2/history/candles"
    params = {
        "symbol": symbol,
        "resolution": "5m",
        "start": start_time,
        "end": end_time
    }
    headers = {"Accept": "application/json"}
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10).json()
        candles = res.get("result", [])
        candles.reverse()
        return candles
    except Exception as e:
        print(f"Fetch Error ({symbol}): {e}")
        return []

def run_scanner():
    ist = pytz.timezone('Asia/Kolkata')
    alerts = []

    for sym in SYMBOLS:
        try:
            candles = get_delta_5m_candles(sym, count=30)
            if len(candles) < 22:
                continue

            # Latest completed 5m candle
            latest_c = candles[-2]
            c_time = datetime.fromtimestamp(latest_c[0], ist).strftime("%H:%M")
            c_open = float(latest_c[1])
            c_high = float(latest_c[2])
            c_low = float(latest_c[3])
            c_close = float(latest_c[4])
            c_vol = float(latest_c[5])

            # Previous 20-Period Avg Volume
            prev_vols = [float(c[5]) for c in candles[-22:-2]]
            avg_vol_20 = sum(prev_vols) / len(prev_vols)

            if avg_vol_20 == 0:
                continue

            vol_ratio = c_vol / avg_vol_20

            # 2X Volume Condition
            if vol_ratio >= 2.0:
                is_bullish = c_close >= c_open
                signal = "🟢 *BUY (Bullish)*" if is_bullish else "🔴 *SELL (Bearish)*"

                alert_text = (
                    f"⚡ *DELTA 5-MIN VOLUME ALERT*\n"
                    f"💎 *Pair:* `{sym}`\n"
                    f"🎯 *Signal:* {signal}\n"
                    f"📊 *Volume:* `{vol_ratio:.1f}x` (Avg: `{avg_vol_20:,.1f}` | Current: `{c_vol:,.1f}`)\n"
                    f"💰 *LTP:* `${c_close:,.2f}`\n"
                    f"⏱ *Candle Time:* `{c_time} IST`"
                )
                alerts.append(alert_text)

        except Exception as e:
            print(f"Error {sym}: {e}")
            continue

    if alerts:
        msg = "\n\n".join(alerts)
        send_telegram(msg)
        print("Alerts sent to Telegram!")
    else:
        print("No 2x volume spikes detected on 5m candle.")

if __name__ == "__main__":
    run_scanner()
