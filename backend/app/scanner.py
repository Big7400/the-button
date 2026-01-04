from typing import List, Dict, Any
from datetime import datetime

class MarketScanner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def scan(self) -> Dict[str, Any]:
        results = []

        for market in self.config["markets"]:
            for timeframe in self.config["timeframes"]:
                scan_result = self.evaluate_market(market, timeframe)
                if scan_result:
                    results.append(scan_result)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }

    def evaluate_market(self, market: str, timeframe: str) -> Dict[str, Any]:
        status = "PENDING"
        reason = []
        confidence = 0.0

        # --------------------------
        # Placeholder price & volume data
        # --------------------------
        close_prices = [100, 102, 101, 103, 105, 104, 106]
        high_prices = [101, 103, 102, 104, 106, 105, 107]
        low_prices = [99, 101, 100, 102, 104, 103, 105]
        volumes = [1200, 1500, 1300, 1600, 1700, 1650, 1800]

        # --------------------------
        # EMA Logic
        # --------------------------
        ema_50 = sum(close_prices[-min(50, len(close_prices)):]) / min(50, len(close_prices))
        ema_200 = sum(close_prices[-min(200, len(close_prices)):]) / min(200, len(close_prices))
        if ema_50 > ema_200:
            reason.append("EMA indicates uptrend")
            confidence += 0.1
        else:
            reason.append("EMA indicates downtrend")
            confidence += 0.1

        # --------------------------
        # MACD Logic
        # --------------------------
        fast_length = self.config["indicators"]["macd"]["fast"]
        slow_length = self.config["indicators"]["macd"]["slow"]
        signal_length = self.config["indicators"]["macd"]["signal"]
        fast_ma = sum(close_prices[-min(fast_length, len(close_prices)):]) / min(fast_length, len(close_prices))
        slow_ma = sum(close_prices[-min(slow_length, len(close_prices)):]) / min(slow_length, len(close_prices))
        macd_line = fast_ma - slow_ma
        signal_line = macd_line * 0.8
        if macd_line > signal_line:
            reason.append("MACD bullish")
            confidence += 0.1
        else:
            reason.append("MACD bearish")
            confidence += 0.1

        # --------------------------
        # RSI Logic
        # --------------------------
        rsi_period = self.config["indicators"]["rsi"]["period"]
        gains, losses = [], []
        for i in range(1, len(close_prices)):
            change = close_prices[i] - close_prices[i-1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))
        avg_gain = sum(gains)/rsi_period if gains else 0
        avg_loss = sum(losses)/rsi_period if losses else 0
        rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
        if rsi > 70:
            reason.append("RSI overbought")
            confidence -= 0.05
        elif rsi < 30:
            reason.append("RSI oversold")
            confidence += 0.05
        else:
            reason.append("RSI neutral")
            confidence += 0.05

        # --------------------------
        # Volume Logic
        # --------------------------
        avg_volume = sum(volumes)/len(volumes)
        current_volume = volumes[-1]
        if current_volume > avg_volume:
            reason.append("Volume higher than average")
            confidence += 0.05
        else:
            reason.append("Volume lower than average")
            confidence -= 0.05

        # --------------------------
        # ATR / Volatility Logic
        # --------------------------
        tr_list = [max(high_prices[i]-low_prices[i], abs(high_prices[i]-close_prices[i-1]), abs(low_prices[i]-close_prices[i-1])) for i in range(1, len(close_prices))]
        atr = sum(tr_list)/len(tr_list) if tr_list else 0
        reason.append(f"ATR placeholder: {round(atr, 2)}")
        confidence += 0.05

        # --------------------------
        # Pivot Points Logic (placeholder)
        # --------------------------
        pivot = (high_prices[-1] + low_prices[-1] + close_prices[-1]) / 3
        reason.append(f"Pivot Point placeholder: {round(pivot, 2)}")
        confidence += 0.03

        # --------------------------
        # VWAP Logic (placeholder)
        # --------------------------
        typical_prices = [(high_prices[i] + low_prices[i] + close_prices[i])/3 for i in range(len(close_prices))]
        vwap = sum([typical_prices[i]*volumes[i] for i in range(len(close_prices))]) / sum(volumes)
        reason.append(f"VWAP placeholder: {round(vwap, 2)}")
        confidence += 0.03

        # --------------------------
        # Supertrend Logic (placeholder)
        # --------------------------
        supertrend = ema_50 + atr  # simplified placeholder
        reason.append(f"Supertrend placeholder: {round(supertrend, 2)}")
        confidence += 0.03

        # --------------------------
        # Final Status
        # --------------------------
        if confidence >= 0.7:
            status = "GREEN"
        elif confidence >= 0.4:
            status = "YELLOW"
        else:
            status = "RED"

        return {
            "market": market,
            "timeframe": timeframe,
            "status": status,
            "reason": reason,
            "confidence": round(confidence, 2)
        }


# --------------------------
# Test the scanner
# --------------------------
if __name__ == "__main__":
    test_config = {
        "markets": ["XAUUSD", "EURUSD", "BTC-USD"],
        "timeframes": ["5m", "15m"],
        "indicators": {
            "ema": {"periods": [50, 200], "buffer_pct": 0.0},
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "rsi": {"period": 14},
            "atr": {"period": 14},
            "volume": {},
            "pivot": {},
            "vwap": {},
            "supertrend": {}
        }
    }

    scanner = MarketScanner(test_config)
    print(scanner.scan())
