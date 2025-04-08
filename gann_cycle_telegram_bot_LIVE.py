
import yfinance as yf
import pandas as pd
import telegram
from telegram.ext import Updater, CommandHandler

# Gann Cycle Detection
GANN_CYCLES = [30, 45, 60, 90, 120, 144, 180, 225, 240, 270, 288, 315, 360]
TOLERANCE = 10
MIN_CYCLE_DAYS = 15

def score_cycle(price1, price2, actual_days, expected_days):
    time_accuracy = 1 - (abs(actual_days - expected_days) / expected_days)
    price_change = abs(price2 - price1)
    magnitude_score = min(price_change / 10, 1)
    return round((time_accuracy * 0.6 + magnitude_score * 0.4) * 100, 2)

def detect_cycles(data):
    pivots = []
    cycles = []
    lows = data['Low'].values
    index = data.index

    for i in range(2, len(data) - 2):
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            pivots.append((index[i], lows[i]))

    for j in range(1, len(pivots)):
        date1, price1 = pivots[j - 1]
        date2, price2 = pivots[j]
        duration = (date2 - date1).days

        if duration >= MIN_CYCLE_DAYS:
            for gc in GANN_CYCLES:
                if abs(duration - gc) <= TOLERANCE:
                    cycle = {
                        'from': date1.strftime("%Y-%m-%d"),
                        'to': date2.strftime("%Y-%m-%d"),
                        'duration': duration,
                        'cycle_match': gc,
                        'deviation': duration - gc,
                        'confidence': score_cycle(price1, price2, duration, gc)
                    }
                    cycles.append(cycle)

    return cycles

# Telegram Bot Token
TELEGRAM_TOKEN = '8053193556:AAHB0nOly_iqGcndXT29d1JEll_Sc57DSJQ'

# Define command
def start(update, context):
    update.message.reply_text("Welcome to Gann Cycle Bot! Use /nifty to analyze NIFTY 50.")

def analyze_nifty(update, context):
    data = yf.download("^NSEI", period="1y", interval="1d")
    if data.empty:
        update.message.reply_text("Failed to fetch NIFTY data.")
        return

    cycles = detect_cycles(data)
    if not cycles:
        update.message.reply_text("No strong Gann cycles detected.")
    else:
        msg = "Top Gann Cycles Detected:\n"
        for c in cycles[-3:]:
            msg += f"From {c['from']} to {c['to']} | Days: {c['duration']} | Match: {c['cycle_match']} | Confidence: {c['confidence']}%\n"
        update.message.reply_text(msg)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("nifty", analyze_nifty))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
