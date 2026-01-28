import tkinter as tk
from tkinter import ttk
import ccxt
import pandas as pd
import threading
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ===================== КОНФИГ =====================
BG = "#0b0f14"
PANEL = "#131722"
CARD = "#1e222d"
ACCENT = "#2962ff"
TEXT = "#d1d4dc"
LONG_COLOR = "#26a69a"
SHORT_COLOR = "#ef5350"
NEUTRAL_COLOR = "#999999"

FONT = ("Segoe UI", 10)
BIG = ("Segoe UI", 16, "bold")

# Топ-50 монет (примерно)
TOP_COINS = ["BTC/USDT","ETH/USDT","SOL/USDT","AVAX/USDT","ARB/USDT",
             "MATIC/USDT","BNB/USDT","LTC/USDT","DOGE/USDT","XRP/USDT",
             "ADA/USDT","ATOM/USDT","DOT/USDT","LINK/USDT","TRX/USDT",
             "FIL/USDT","UNI/USDT","SAND/USDT","APE/USDT","MANA/USDT",
             "GALA/USDT","VET/USDT","FTM/USDT","NEAR/USDT","ALGO/USDT",
             "XTZ/USDT","ICP/USDT","EOS/USDT","KSM/USDT","EGLD/USDT",
             "THETA/USDT","AXS/USDT","CRV/USDT","CHZ/USDT","1INCH/USDT",
             "RUNE/USDT","AAVE/USDT","FLOW/USDT","KAVA/USDT","LDO/USDT",
             "STX/USDT","ZEC/USDT","BNX/USDT","BTG/USDT","MIOTA/USDT",
             "COMP/USDT","CEL/USDT","HNT/USDT","ENJ/USDT","BAT/USDT"]

# ===================== ПРИЛОЖЕНИЕ =====================
class ScannerPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("💎 Crypto Market Scanner PRO")
        self.geometry("1400x800")
        self.configure(bg=BG)

        self.selected_coin = TOP_COINS[0]
        self.binance = ccxt.binance()
        self.data_cache = {}  # хранение предыдущих значений для стабильной таблицы
        self.create_layout()
        self.update_data_thread()
        self.mainloop()

    # ===================== ЛАЙАУТ =====================
    def create_layout(self):
        # Боковое меню
        self.sidebar = tk.Frame(self, bg=PANEL, width=220)
        self.sidebar.pack(side="left", fill="y")

        tk.Label(self.sidebar, text="MARKET SCANNER PRO", bg=PANEL,
                 fg=ACCENT, font=BIG).pack(pady=20)

        tk.Button(self.sidebar, text="Обновить", bg=ACCENT, fg="white",
                  font=FONT, command=self.refresh_data).pack(pady=10, padx=10, fill="x")

        # Основная область
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="right", expand=True, fill="both")

        # Таблица
        columns = ("symbol","price","rsi","ema20","macd","boll_signal","obv","signal","strength")
        self.tree = ttk.Treeview(self.main, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col.upper())
        self.tree.pack(padx=20, pady=20, fill="x")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_coin)

        # Цвета таблицы
        style = ttk.Style()
        style.configure("Treeview", background=CARD, foreground=TEXT, fieldbackground=CARD, font=FONT)
        style.map("Treeview", background=[("selected", ACCENT)])

        # График выбранной монеты
        self.fig = plt.Figure(figsize=(10,4))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(CARD)
        self.canvas = FigureCanvasTkAgg(self.fig, self.main)
        self.canvas.get_tk_widget().pack(padx=20, pady=10, fill="both", expand=True)

        # Кнопки сигналов
        self.button_frame = tk.Frame(self.main, bg=BG)
        self.button_frame.pack(pady=10)

        self.long_btn = tk.Button(self.button_frame, text="ЛОНГ", bg=LONG_COLOR, fg="white",
                                  font=("Segoe UI", 16, "bold"), width=12)
        self.long_btn.pack(side="left", padx=20)

        self.short_btn = tk.Button(self.button_frame, text="ШОРТ", bg=SHORT_COLOR, fg="white",
                                   font=("Segoe UI", 16, "bold"), width=12)
        self.short_btn.pack(side="left", padx=20)

    # ===================== ОБНОВЛЕНИЕ ДАННЫХ =====================
    def refresh_data(self):
        for symbol in TOP_COINS:
            try:
                ohlcv = self.binance.fetch_ohlcv(symbol, timeframe="1h", limit=50)
                df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","vol"])
                df["ema20"] = df["close"].ewm(span=20).mean()
                df["rsi"] = self.rsi(df["close"],14)
                macd_line, signal_line = self.macd(df["close"])
                df["macd"] = macd_line
                df["boll_signal"] = self.bollinger_signal(df["close"])
                df["obv"] = self.obv(df["close"], df["vol"])

                price = df["close"].iloc[-1]
                ema20 = df["ema20"].iloc[-1]
                rsi = df["rsi"].iloc[-1]
                macd_val = df["macd"].iloc[-1]
                boll_val = df["boll_signal"].iloc[-1]
                obv_val = df["obv"].iloc[-1]

                # Сигнал
                signal, strength = self.calc_signal(rsi, price, ema20, macd_val, boll_val, obv_val)

                # Обновляем таблицу только значениями
                if symbol in self.data_cache:
                    item_id = self.data_cache[symbol]
                    self.tree.item(item_id, values=(symbol, round(price,2), round(rsi,1), round(ema20,2),
                                                    round(macd_val,2), boll_val, round(obv_val,0), signal, f"{strength}%"))
                else:
                    item_id = self.tree.insert("", tk.END, values=(symbol, round(price,2), round(rsi,1), round(ema20,2),
                                                                   round(macd_val,2), boll_val, round(obv_val,0), signal, f"{strength}%"),
                                               tags=(signal,))
                    self.data_cache[symbol] = item_id
                    self.tree.tag_configure("ЛОНГ", foreground=LONG_COLOR)
                    self.tree.tag_configure("ШОРТ", foreground=SHORT_COLOR)
                    self.tree.tag_configure("НЕЙТРАЛЬНО", foreground=NEUTRAL_COLOR)

                # Обновляем график выбранной монеты
                if symbol == self.selected_coin:
                    self.plot_graph(df, symbol)

            except Exception as e:
                print(symbol, "ошибка:", e)

    # ===================== RSI =====================
    def rsi(self, series, period):
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -1*delta.clip(upper=0)
        ma_up = up.ewm(com=period-1, adjust=True).mean()
        ma_down = down.ewm(com=period-1, adjust=True).mean()
        rsi = 100 - (100/(1+ma_up/ma_down))
        return rsi

    # ===================== MACD =====================
    def macd(self, series, fast=12, slow=26, signal=9):
        exp1 = series.ewm(span=fast, adjust=False).mean()
        exp2 = series.ewm(span=slow, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return macd_line, signal_line

    # ===================== Bollinger Bands =====================
    def bollinger_signal(self, series, window=20, dev=2):
        ma = series.rolling(window).mean()
        std = series.rolling(window).std()
        upper = ma + dev*std
        lower = ma - dev*std
        last = series.iloc[-1]
        if last > upper.iloc[-1]:
            return "ШОРТ"
        elif last < lower.iloc[-1]:
            return "ЛОНГ"
        else:
            return "НЕЙТРАЛЬНО"

    # ===================== OBV =====================
    def obv(self, close, volume):
        obv = [0]
        for i in range(1,len(close)):
            if close[i] > close[i-1]:
                obv.append(obv[-1]+volume[i])
            elif close[i] < close[i-1]:
                obv.append(obv[-1]-volume[i])
            else:
                obv.append(obv[-1])
        return pd.Series(obv)

    # ===================== СИГНАЛ =====================
    def calc_signal(self, rsi, price, ema20, macd_val, boll_val, obv_val):
        score = 0
        if rsi < 30: score += 1
        elif rsi > 70: score -= 1
        if price > ema20: score += 1
        else: score -= 1
        if macd_val > 0: score +=1
        else: score -=1
        if boll_val == "ЛОНГ": score +=1
        elif boll_val == "ШОРТ": score -=1
        if obv_val > 0: score +=1
        else: score -=1

        if score > 0:
            return "ЛОНГ", min(score*20,100)
        elif score < 0:
            return "ШОРТ", min(-score*20,100)
        else:
            return "НЕЙТРАЛЬНО", 0

    # ===================== КЛИК ПО ТАБЛИЦЕ =====================
    def on_select_coin(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            self.selected_coin = item["values"][0]
            ohlcv = self.binance.fetch_ohlcv(self.selected_coin, timeframe="1h", limit=50)
            df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","vol"])
            df["ema20"] = df["close"].ewm(span=20).mean()
            df["rsi"] = self.rsi(df["close"],14)
            self.plot_graph(df, self.selected_coin)

    # ===================== ГРАФИК =====================
    def plot_graph(self, df, symbol):
        self.ax.clear()
        self.ax.plot(df["close"], color=ACCENT, label="Close")
        self.ax.plot(df["ema20"], color=LONG_COLOR, label="EMA20")
        self.ax.set_title(symbol, color=TEXT)
        self.ax.tick_params(colors=TEXT)
        self.ax.legend()
        self.canvas.draw()

    # ===================== ФОН ОБНОВЛЕНИЯ =====================
    def update_data_thread(self):
        def run():
            while True:
                self.refresh_data()
                self.after(60000, lambda: None)
        t = threading.Thread(target=run, daemon=True)
        t.start()

# ===================== СТАРТ =====================
ScannerPro()
