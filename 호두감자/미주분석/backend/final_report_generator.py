#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Report Generator - Creates the Top 10 investment report
"""

import os, json, logging
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinalReportGenerator:
    def __init__(self, data_dir='./data'):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
    def run(self, top_n=10):
        logger.info("🚀 Generating Final Report...")
        
        # Load Quant Data
        stats_path = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
        if not os.path.exists(stats_path):
            logger.error(f"❌ {stats_path} not found")
            return
        
        df = pd.read_csv(stats_path)
        
        # Load AI Data
        ai_path = os.path.join(self.data_dir, 'ai_summaries.json')
        ai_data = {}
        if os.path.exists(ai_path):
            with open(ai_path, encoding='utf-8') as f: 
                ai_data = json.load(f)
        
        results = []
        for _, row in df.iterrows():
            ticker = row['ticker']
            summary = ai_data.get(ticker, {}).get('summary', '')
            
            # AI Bonus Score
            ai_score = 0
            rec = "Hold"
            if "매수" in summary or "Buy" in summary: 
                ai_score = 10
                rec = "Buy"
            if "적극" in summary or "Strong" in summary:
                ai_score = 20
                rec = "Strong Buy"
            if "주의" in summary or "caution" in summary.lower():
                ai_score = -10
                rec = "Caution"
                
            final_score = row['composite_score'] * 0.8 + ai_score
            
            results.append({
                'ticker': ticker,
                'name': row.get('name', ticker),
                'final_score': round(final_score, 1),
                'quant_score': row['composite_score'],
                'grade': row.get('grade', 'N/A'),
                'ai_recommendation': rec,
                'current_price': row.get('current_price', 0),
                'target_upside': row.get('target_upside', 0),
                'sector': row.get('sector', 'N/A'),
                'ai_summary': summary[:200] if summary else ''
            })
        
        # Sort and Rank
        results.sort(key=lambda x: x['final_score'], reverse=True)
        top_picks = results[:top_n]
        for i, p in enumerate(top_picks, 1): 
            p['rank'] = i
        
        # Save Report
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_analyzed': len(results),
            'top_picks': top_picks
        }
        
        output_file = os.path.join(self.data_dir, 'final_top10_report.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Also save for dashboard
        dashboard_file = os.path.join(self.data_dir, 'smart_money_current.json')
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump({'picks': top_picks}, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {output_file}")
        logger.info(f"✅ Saved {dashboard_file}")
        
        # Print summary
        logger.info(f"\n🔥 TOP {top_n} PICKS:")
        for p in top_picks:
            logger.info(f"   #{p['rank']} {p['ticker']}: Score {p['final_score']} | {p['grade']}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--top', type=int, default=10)
    args = parser.parse_args()
    FinalReportGenerator().run(top_n=args.top)
