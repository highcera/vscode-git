#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portfolio Risk Analyzer - Correlation and Volatility Analysis
"""

import os, json, logging
import pandas as pd
import numpy as np
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortfolioRiskAnalyzer:
    def __init__(self, data_dir: str = './data'):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.output_file = os.path.join(data_dir, 'portfolio_risk.json')
    
    def analyze_portfolio(self, tickers: list) -> dict:
        try:
            logger.info(f"📊 Analyzing portfolio risk for {len(tickers)} stocks...")
            data = yf.download(tickers, period='6mo', progress=False)['Close']
            returns = data.pct_change().dropna()
            
            # Correlation matrix
            corr = returns.corr()
            high_corr = []
            cols = corr.columns
            for i in range(len(cols)):
                for j in range(i+1, len(cols)):
                    if corr.iloc[i, j] > 0.8:
                        high_corr.append([cols[i], cols[j], round(corr.iloc[i, j], 2)])
            
            # Portfolio volatility (equal weight)
            cov = returns.cov() * 252
            weights = np.array([1/len(tickers)] * len(tickers))
            var = np.dot(weights.T, np.dot(cov, weights))
            vol = np.sqrt(var)
            
            # Individual volatilities
            individual_vol = (returns.std() * np.sqrt(252) * 100).round(2).to_dict()
            
            result = {
                'timestamp': pd.Timestamp.now().isoformat(),
                'portfolio_volatility': round(vol * 100, 2),
                'high_correlations': high_corr,
                'individual_volatility': individual_vol,
                'risk_level': 'High' if vol > 0.25 else 'Medium' if vol > 0.15 else 'Low'
            }
            
            with open(self.output_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"✅ Saved {self.output_file}")
            logger.info(f"   Portfolio Volatility: {vol*100:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return {'error': str(e)}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--tickers', nargs='+', default=['AAPL', 'NVDA', 'MSFT', 'GOOGL', 'AMZN'])
    args = parser.parse_args()
    PortfolioRiskAnalyzer().analyze_portfolio(args.tickers)

if __name__ == "__main__":
    main()
