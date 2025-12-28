#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sector Performance Heatmap Data Collector
Collects sector ETF performance for visualization
"""

import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SectorHeatmapCollector:
    """Collect sector ETF performance data for heatmap visualization"""
    
    def __init__(self, data_dir: str = './data'):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.output_file = os.path.join(data_dir, 'sector_heatmap.json')
        
        # Sector ETFs with full names
        self.sector_etfs = {
            'XLK': {'name': 'Technology', 'color': '#4A90A4'},
            'XLF': {'name': 'Financials', 'color': '#6B8E23'},
            'XLV': {'name': 'Healthcare', 'color': '#FF69B4'},
            'XLE': {'name': 'Energy', 'color': '#FF6347'},
            'XLY': {'name': 'Consumer Disc.', 'color': '#FFD700'},
            'XLP': {'name': 'Consumer Staples', 'color': '#98D8C8'},
            'XLI': {'name': 'Industrials', 'color': '#DDA0DD'},
            'XLB': {'name': 'Materials', 'color': '#F0E68C'},
            'XLU': {'name': 'Utilities', 'color': '#87CEEB'},
            'XLRE': {'name': 'Real Estate', 'color': '#CD853F'},
            'XLC': {'name': 'Comm. Services', 'color': '#9370DB'},
        }
        
        # Sector stocks for detail map
        self.sector_stocks = {
            'Technology': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'AMD', 'ADBE', 'CSCO', 'INTC'],
            'Financials': ['BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'SCHW', 'AXP'],
            'Healthcare': ['UNH', 'JNJ', 'LLY', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL'],
            'Consumer Disc.': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TJX', 'BKNG', 'CMG'],
            'Consumer Staples': ['PG', 'KO', 'PEP', 'COST', 'WMT', 'PM', 'MO', 'CL', 'EL', 'GIS'],
            'Industrials': ['CAT', 'RTX', 'UNP', 'HON', 'DE', 'BA', 'GE', 'LMT', 'UPS', 'MMM'],
            'Materials': ['LIN', 'APD', 'SHW', 'FCX', 'NEM', 'ECL', 'DD', 'NUE', 'DOW', 'CTVA'],
            'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'SRE', 'EXC', 'XEL', 'ED', 'WEC'],
            'Real Estate': ['PLD', 'AMT', 'EQIX', 'CCI', 'PSA', 'O', 'SPG', 'WELL', 'DLR', 'AVB'],
            'Comm. Services': ['META', 'GOOGL', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR', 'EA'],
        }
    
    def get_sector_etf_performance(self, period: str = '5d') -> List[Dict]:
        """Get performance of sector ETFs"""
        logger.info(f"📊 Fetching sector ETF performance ({period})...")
        
        results = []
        tickers = list(self.sector_etfs.keys())
        
        try:
            data = yf.download(tickers, period=period, progress=False)
            
            for ticker, info in self.sector_etfs.items():
                try:
                    if ticker not in data['Close'].columns:
                        continue
                    
                    prices = data['Close'][ticker].dropna()
                    if len(prices) < 2:
                        continue
                    
                    current = prices.iloc[-1]
                    prev = prices.iloc[-2]
                    first = prices.iloc[0]
                    
                    daily_change = ((current / prev) - 1) * 100
                    period_change = ((current / first) - 1) * 100
                    
                    results.append({
                        'ticker': ticker,
                        'name': info['name'],
                        'color': info['color'],
                        'price': round(current, 2),
                        'daily_change': round(daily_change, 2),
                        'period_change': round(period_change, 2),
                        'change_color': self._get_color(daily_change)
                    })
                    
                except Exception as e:
                    logger.debug(f"Error processing {ticker}: {e}")
                    continue
            
            # Sort by daily change
            results.sort(key=lambda x: x['daily_change'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error fetching ETF data: {e}")
        
        return results
    
    def get_full_market_map(self, period: str = '5d') -> Dict:
        """Get full market map data (Sectors -> Stocks) for Treemap"""
        logger.info(f"📊 Fetching full market map data ({period})...")
        
        all_tickers = []
        ticker_to_sector = {}
        
        for sector, stocks in self.sector_stocks.items():
            all_tickers.extend(stocks)
            for stock in stocks:
                ticker_to_sector[stock] = sector
                
        try:
            data = yf.download(all_tickers, period=period, progress=False)
            
            if data.empty:
                return {'error': 'No data'}
            
            market_map = {name: [] for name in self.sector_stocks.keys()}
            
            for ticker in all_tickers:
                try:
                    if ticker not in data['Close'].columns:
                        continue
                    
                    prices = data['Close'][ticker].dropna()
                    if len(prices) < 2:
                        continue
                    
                    current = prices.iloc[-1]
                    prev = prices.iloc[-2]
                    change = ((current / prev) - 1) * 100
                    
                    # Weight by Volume * Price (Activity proxy)
                    vol = data['Volume'][ticker].iloc[-1] if 'Volume' in data.columns else 100000
                    weight = current * vol
                    
                    sector = ticker_to_sector.get(ticker, 'Unknown')
                    if sector in market_map:
                        market_map[sector].append({
                            'x': ticker,
                            'y': round(weight, 0),
                            'price': round(current, 2),
                            'change': round(change, 2),
                            'color': self._get_color(change)
                        })
                except:
                    pass
            
            series = []
            for sector_name, stocks in market_map.items():
                if stocks:
                    stocks.sort(key=lambda x: x['y'], reverse=True)
                    series.append({'name': sector_name, 'data': stocks})
            
            series.sort(key=lambda s: sum(i['y'] for i in s['data']), reverse=True)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'period': period,
                'series': series
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {'error': str(e)}
            
    def _get_color(self, change: float) -> str:
        """Get color based on change percentage"""
        if change >= 3: return '#00C853'
        elif change >= 1: return '#4CAF50'
        elif change >= 0: return '#81C784'
        elif change >= -1: return '#EF9A9A'
        elif change >= -3: return '#F44336'
        else: return '#B71C1C'
    
    def run(self, period: str = '5d') -> Dict:
        """Run full collection and save data"""
        logger.info("🚀 Starting Sector Heatmap Collection...")
        
        # Get sector ETF performance
        etf_performance = self.get_sector_etf_performance(period)
        
        # Get detailed market map
        market_map = self.get_full_market_map(period)
        
        # Create output
        output = {
            'timestamp': datetime.now().isoformat(),
            'period': period,
            'sector_etfs': etf_performance,
            'market_map': market_map.get('series', []),
            'summary': {
                'top_sector': etf_performance[0]['name'] if etf_performance else None,
                'bottom_sector': etf_performance[-1]['name'] if etf_performance else None,
                'avg_change': round(sum(e['daily_change'] for e in etf_performance) / len(etf_performance), 2) if etf_performance else 0
            }
        }
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved to {self.output_file}")
        
        # Print summary
        logger.info("\n📊 Sector Performance Summary:")
        for etf in etf_performance[:5]:
            arrow = "🟢" if etf['daily_change'] >= 0 else "🔴"
            logger.info(f"   {arrow} {etf['name']}: {etf['daily_change']:+.2f}%")
        
        return output


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Sector Heatmap Collector')
    parser.add_argument('--dir', default='./data', help='Data directory')
    parser.add_argument('--period', default='5d', help='Time period (1d, 5d, 1mo)')
    args = parser.parse_args()
    
    collector = SectorHeatmapCollector(data_dir=args.dir)
    collector.run(period=args.period)


if __name__ == "__main__":
    main()
