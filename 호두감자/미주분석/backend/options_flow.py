#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Options Flow Analyzer
Tracks options volume and unusual activity for key stocks
"""

import os
import json
import logging
import yfinance as yf
from datetime import datetime
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OptionsFlowAnalyzer:
    """Analyze options flow for unusual activity detection"""
    
    def __init__(self, data_dir: str = './data'):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.output_file = os.path.join(data_dir, 'options_flow.json')
        
        # Key stocks to monitor
        self.watchlist = [
            'AAPL', 'NVDA', 'TSLA', 'MSFT', 'AMZN', 'META', 'GOOGL', 
            'SPY', 'QQQ', 'AMD', 'NFLX', 'BA', 'DIS', 'COIN', 'PLTR'
        ]
    
    def get_options_summary(self, ticker: str) -> Dict:
        """Get options summary for a single ticker"""
        try:
            stock = yf.Ticker(ticker)
            exps = stock.options
            
            if not exps:
                return {'ticker': ticker, 'error': 'No options available'}
            
            # Get nearest expiration
            opt = stock.option_chain(exps[0])
            calls, puts = opt.calls, opt.puts
            
            # Volume and Open Interest
            call_vol = calls['volume'].sum() if 'volume' in calls.columns else 0
            put_vol = puts['volume'].sum() if 'volume' in puts.columns else 0
            call_oi = calls['openInterest'].sum() if 'openInterest' in calls.columns else 0
            put_oi = puts['openInterest'].sum() if 'openInterest' in puts.columns else 0
            
            # Handle NaN
            call_vol = int(call_vol) if not pd.isna(call_vol) else 0
            put_vol = int(put_vol) if not pd.isna(put_vol) else 0
            call_oi = int(call_oi) if not pd.isna(call_oi) else 0
            put_oi = int(put_oi) if not pd.isna(put_oi) else 0
            
            # Put/Call Ratio
            pc_ratio = put_vol / call_vol if call_vol > 0 else 0
            
            # Unusual activity detection
            avg_call_vol = calls['volume'].mean() if 'volume' in calls.columns else 1
            avg_put_vol = puts['volume'].mean() if 'volume' in puts.columns else 1
            
            unusual_calls = len(calls[calls['volume'] > avg_call_vol * 3]) if 'volume' in calls.columns else 0
            unusual_puts = len(puts[puts['volume'] > avg_put_vol * 3]) if 'volume' in puts.columns else 0
            
            # Sentiment
            if pc_ratio < 0.5:
                sentiment = "Bullish"
            elif pc_ratio > 1.5:
                sentiment = "Bearish"
            else:
                sentiment = "Neutral"
            
            # Max pain calculation (simplified)
            try:
                # Find strike with most open interest
                all_strikes = set(calls['strike'].tolist() + puts['strike'].tolist())
                max_pain_strike = None
                min_pain = float('inf')
                
                current_price = stock.info.get('currentPrice', 0) or stock.info.get('regularMarketPrice', 0) or 0
                
                for strike in all_strikes:
                    call_pain = calls[calls['strike'] >= strike]['openInterest'].sum() * (strike - current_price) if current_price else 0
                    put_pain = puts[puts['strike'] <= strike]['openInterest'].sum() * (current_price - strike) if current_price else 0
                    total_pain = abs(call_pain) + abs(put_pain)
                    
                    if total_pain < min_pain:
                        min_pain = total_pain
                        max_pain_strike = strike
            except:
                max_pain_strike = None
            
            return {
                'ticker': ticker,
                'expiration': exps[0],
                'metrics': {
                    'pc_ratio': round(pc_ratio, 2),
                    'call_volume': call_vol,
                    'put_volume': put_vol,
                    'call_oi': call_oi,
                    'put_oi': put_oi,
                    'total_volume': call_vol + put_vol
                },
                'unusual': {
                    'unusual_calls': unusual_calls,
                    'unusual_puts': unusual_puts,
                    'has_unusual': unusual_calls > 0 or unusual_puts > 0
                },
                'sentiment': sentiment,
                'max_pain': max_pain_strike
            }
            
        except Exception as e:
            logger.debug(f"Error analyzing {ticker}: {e}")
            return {'ticker': ticker, 'error': str(e)}
    
    def analyze_watchlist(self) -> List[Dict]:
        """Analyze all stocks in watchlist"""
        logger.info("📊 Analyzing options flow...")
        
        results = []
        
        for ticker in self.watchlist:
            logger.info(f"   Analyzing {ticker}...")
            result = self.get_options_summary(ticker)
            if 'error' not in result:
                results.append(result)
        
        # Sort by total volume
        results.sort(key=lambda x: x['metrics']['total_volume'], reverse=True)
        
        return results
    
    def run(self) -> Dict:
        """Run analysis and save results"""
        logger.info("🚀 Starting Options Flow Analysis...")
        
        results = self.analyze_watchlist()
        
        # Create output
        output = {
            'timestamp': datetime.now().isoformat(),
            'options_flow': results,
            'summary': {
                'total_analyzed': len(results),
                'bullish_count': len([r for r in results if r.get('sentiment') == 'Bullish']),
                'bearish_count': len([r for r in results if r.get('sentiment') == 'Bearish']),
                'unusual_activity': [r['ticker'] for r in results if r.get('unusual', {}).get('has_unusual', False)]
            }
        }
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"✅ Saved to {self.output_file}")
        
        # Print summary
        logger.info("\n📊 Options Flow Summary:")
        for result in results[:5]:
            metrics = result.get('metrics', {})
            sentiment = result.get('sentiment', 'N/A')
            emoji = "🟢" if sentiment == "Bullish" else ("🔴" if sentiment == "Bearish" else "⚪")
            logger.info(f"   {emoji} {result['ticker']}: P/C Ratio {metrics.get('pc_ratio', 0):.2f} ({sentiment})")
        
        unusual = output['summary']['unusual_activity']
        if unusual:
            logger.info(f"\n⚠️ Unusual Activity Detected: {', '.join(unusual)}")
        
        return output


# Need to import pandas
import pandas as pd


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Options Flow Analyzer')
    parser.add_argument('--dir', default='./data', help='Data directory')
    parser.add_argument('--tickers', nargs='+', help='Override watchlist')
    args = parser.parse_args()
    
    analyzer = OptionsFlowAnalyzer(data_dir=args.dir)
    
    if args.tickers:
        analyzer.watchlist = args.tickers
    
    analyzer.run()


if __name__ == "__main__":
    main()
