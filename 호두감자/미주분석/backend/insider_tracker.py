#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insider Tracker - Tracks insider buying/selling activity
"""

import os, json, logging
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsiderTracker:
    def __init__(self, data_dir: str = './data'):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.output_file = os.path.join(data_dir, 'insider_moves.json')
    
    def get_insider_activity(self, ticker: str) -> List[Dict]:
        try:
            stock = yf.Ticker(ticker)
            df = stock.insider_transactions
            if df is None or df.empty: return []
            
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=180)
            recent = []
            
            for date, row in df.sort_index(ascending=False).iterrows():
                if isinstance(date, pd.Timestamp) and date < cutoff: continue
                text = str(row.get('Text', '')).lower()
                is_buy = 'purchase' in text or 'buy' in text
                is_sell = 'sale' in text or 'sell' in text
                if not is_buy and not is_sell: continue
                
                recent.append({
                    'date': str(date.date()) if hasattr(date, 'date') else str(date),
                    'insider': str(row.get('Insider', 'N/A')),
                    'type': 'Buy' if is_buy else 'Sell',
                    'value': float(row.get('Value', 0) or 0),
                    'shares': int(row.get('Shares', 0) or 0)
                })
            return recent[:10]
        except: return []
    
    def analyze_tickers(self, tickers: List[str]) -> Dict:
        results = {}
        for ticker in tickers:
            txns = self.get_insider_activity(ticker)
            if txns:
                buy_val = sum(t['value'] for t in txns if t['type'] == 'Buy')
                sell_val = sum(t['value'] for t in txns if t['type'] == 'Sell')
                score = 50 + (15 if buy_val > sell_val else -10 if sell_val > buy_val else 0)
                results[ticker] = {'score': score, 'transactions': txns[:5]}
        return results
    
    def run(self, tickers: List[str] = None) -> Dict:
        logger.info("🚀 Starting Insider Tracker...")
        if tickers is None:
            tickers = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'AMZN', 'META', 'GOOGL']
        
        details = self.analyze_tickers(tickers)
        output = {'timestamp': datetime.now().isoformat(), 'details': details}
        
        with open(self.output_file, 'w') as f:
            json.dump(output, f, indent=2)
        logger.info(f"✅ Saved {self.output_file}")
        return output

if __name__ == "__main__":
    InsiderTracker().run()
