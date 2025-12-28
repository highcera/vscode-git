#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US ETF Flow Analysis
Tracks fund flows into major ETFs and generates AI insights
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETFFlowAnalyzer:
    """Analyze ETF fund flows and generate insights"""
    
    def __init__(self, data_dir: str = './data'):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.output_csv = os.path.join(data_dir, 'us_etf_flows.csv')
        self.output_json = os.path.join(data_dir, 'etf_flow_analysis.json')
        
        # 24 Major ETFs to track
        self.etf_list = {
            # Broad Market
            'SPY': {'name': 'S&P 500 SPDR', 'category': 'Broad Market'},
            'QQQ': {'name': 'Invesco QQQ Trust', 'category': 'Tech/Growth'},
            'IWM': {'name': 'iShares Russell 2000', 'category': 'Small Cap'},
            'DIA': {'name': 'SPDR Dow Jones', 'category': 'Broad Market'},
            'VTI': {'name': 'Vanguard Total Stock Market', 'category': 'Broad Market'},
            
            # Sector ETFs
            'XLK': {'name': 'Technology Select Sector', 'category': 'Sector'},
            'XLF': {'name': 'Financial Select Sector', 'category': 'Sector'},
            'XLE': {'name': 'Energy Select Sector', 'category': 'Sector'},
            'XLV': {'name': 'Health Care Select Sector', 'category': 'Sector'},
            'XLI': {'name': 'Industrial Select Sector', 'category': 'Sector'},
            'XLY': {'name': 'Consumer Discretionary', 'category': 'Sector'},
            'XLP': {'name': 'Consumer Staples', 'category': 'Sector'},
            'XLU': {'name': 'Utilities Select Sector', 'category': 'Sector'},
            
            # Thematic
            'ARKK': {'name': 'ARK Innovation ETF', 'category': 'Thematic'},
            'SMH': {'name': 'VanEck Semiconductor', 'category': 'Thematic'},
            
            # Fixed Income
            'TLT': {'name': 'iShares 20+ Year Treasury', 'category': 'Bonds'},
            'HYG': {'name': 'iShares High Yield Corporate', 'category': 'Bonds'},
            'LQD': {'name': 'iShares Investment Grade Corp', 'category': 'Bonds'},
            
            # Commodities
            'GLD': {'name': 'SPDR Gold Shares', 'category': 'Commodities'},
            'USO': {'name': 'United States Oil Fund', 'category': 'Commodities'},
            'SLV': {'name': 'iShares Silver Trust', 'category': 'Commodities'},
            
            # International
            'EEM': {'name': 'iShares MSCI Emerging Markets', 'category': 'International'},
            'VEA': {'name': 'Vanguard FTSE Developed Mkts', 'category': 'International'},
            'FXI': {'name': 'iShares China Large-Cap', 'category': 'International'},
        }
    
    def calculate_flow_proxy(self, df: pd.DataFrame) -> Dict:
        """
        Calculate fund flow proxy using price and volume data
        Real ETF flows require premium data, so we use OBV + Price Movement
        """
        if len(df) < 20:
            return None
        
        df = df.sort_values('Date').reset_index(drop=True)
        
        # OBV calculation
        obv = [0]
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                obv.append(obv[-1] + df['Volume'].iloc[i])
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                obv.append(obv[-1] - df['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        # Recent metrics
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        week_ago_price = df['Close'].iloc[-5] if len(df) >= 5 else df['Close'].iloc[0]
        month_ago_price = df['Close'].iloc[-20] if len(df) >= 20 else df['Close'].iloc[0]
        
        # Returns
        daily_return = ((current_price / prev_price) - 1) * 100
        weekly_return = ((current_price / week_ago_price) - 1) * 100
        monthly_return = ((current_price / month_ago_price) - 1) * 100
        
        # Volume analysis
        avg_vol_5d = df['Volume'].tail(5).mean()
        avg_vol_20d = df['Volume'].tail(20).mean()
        vol_ratio = avg_vol_5d / avg_vol_20d if avg_vol_20d > 0 else 1
        
        # OBV trend
        obv_current = obv[-1]
        obv_20d_ago = obv[-20] if len(obv) >= 20 else obv[0]
        obv_change = ((obv_current - obv_20d_ago) / abs(obv_20d_ago)) * 100 if obv_20d_ago != 0 else 0
        
        # Flow Score (0-100)
        score = 50
        
        # Price momentum
        if monthly_return > 5:
            score += 15
        elif monthly_return > 2:
            score += 10
        elif monthly_return < -5:
            score -= 15
        elif monthly_return < -2:
            score -= 10
        
        # OBV trend
        if obv_change > 10:
            score += 15
        elif obv_change > 5:
            score += 8
        elif obv_change < -10:
            score -= 15
        elif obv_change < -5:
            score -= 8
        
        # Volume surge
        if vol_ratio > 1.3:
            score += 10
        elif vol_ratio > 1.1:
            score += 5
        elif vol_ratio < 0.8:
            score -= 5
        
        score = max(0, min(100, score))
        
        # Interpretation
        if score >= 70:
            flow_signal = "Strong Inflow"
        elif score >= 55:
            flow_signal = "Inflow"
        elif score >= 45:
            flow_signal = "Neutral"
        elif score >= 30:
            flow_signal = "Outflow"
        else:
            flow_signal = "Strong Outflow"
        
        return {
            'current_price': round(current_price, 2),
            'daily_return': round(daily_return, 2),
            'weekly_return': round(weekly_return, 2),
            'monthly_return': round(monthly_return, 2),
            'avg_vol_5d': int(avg_vol_5d),
            'avg_vol_20d': int(avg_vol_20d),
            'vol_ratio': round(vol_ratio, 2),
            'obv_change_20d': round(obv_change, 2),
            'flow_score': score,
            'flow_signal': flow_signal
        }
    
    def fetch_etf_data(self) -> pd.DataFrame:
        """Fetch ETF price and volume data"""
        logger.info("📊 Fetching ETF data...")
        
        results = []
        
        for ticker, info in tqdm(self.etf_list.items(), desc="Fetching ETFs"):
            try:
                etf = yf.Ticker(ticker)
                hist = etf.history(period='3mo')
                
                if hist.empty:
                    continue
                
                hist = hist.reset_index()
                flow_data = self.calculate_flow_proxy(hist)
                
                if flow_data:
                    results.append({
                        'ticker': ticker,
                        'name': info['name'],
                        'category': info['category'],
                        **flow_data
                    })
                    
            except Exception as e:
                logger.debug(f"Error fetching {ticker}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    def generate_ai_analysis(self, results_df: pd.DataFrame) -> Dict:
        """Generate AI insights using Gemini"""
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            logger.warning("⚠️ No GOOGLE_API_KEY found. Skipping AI analysis.")
            return {'ai_summary': 'AI analysis not available. Set GOOGLE_API_KEY in .env'}
        
        # Prepare summary for AI
        inflows = results_df[results_df['flow_signal'].str.contains('Inflow')].head(5)
        outflows = results_df[results_df['flow_signal'].str.contains('Outflow')].head(5)
        
        inflow_text = "\n".join([f"- {r['ticker']} ({r['name']}): Score {r['flow_score']}" for _, r in inflows.iterrows()])
        outflow_text = "\n".join([f"- {r['ticker']} ({r['name']}): Score {r['flow_score']}" for _, r in outflows.iterrows()])
        
        prompt = f"""다음 ETF 자금 흐름 데이터를 분석하고 투자 인사이트를 제공해주세요.

유입 상위 ETF:
{inflow_text}

유출 상위 ETF:
{outflow_text}

요청:
1. 현재 자금 흐름의 의미 해석 (2-3문장)
2. 투자자들이 주목하는 섹터/테마 (2-3개)
3. 주의해야 할 리스크 (1-2개)

한국어로 간결하게 작성해주세요."""

        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1000}
            }
            
            response = requests.post(f"{url}?key={api_key}", json=payload, timeout=30)
            
            if response.status_code == 200:
                ai_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                return {'ai_summary': ai_text}
            else:
                logger.warning(f"Gemini API error: {response.status_code}")
                return {'ai_summary': 'AI analysis failed'}
                
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {'ai_summary': f'AI analysis error: {str(e)}'}
    
    def run(self) -> pd.DataFrame:
        """Run ETF flow analysis"""
        logger.info("🚀 Starting ETF Flow Analysis...")
        
        # Fetch and analyze data
        results_df = self.fetch_etf_data()
        
        if results_df.empty:
            logger.error("❌ No ETF data retrieved")
            return pd.DataFrame()
        
        # Sort by flow score
        results_df = results_df.sort_values('flow_score', ascending=False).reset_index(drop=True)
        
        # Save CSV
        results_df.to_csv(self.output_csv, index=False)
        logger.info(f"✅ Saved ETF flows to {self.output_csv}")
        
        # Generate AI analysis
        ai_analysis = self.generate_ai_analysis(results_df)
        
        # Create JSON output
        output = {
            'timestamp': datetime.now().isoformat(),
            'etf_count': len(results_df),
            'top_inflows': results_df.head(5).to_dict('records'),
            'top_outflows': results_df.tail(5).to_dict('records'),
            'by_category': {},
            **ai_analysis
        }
        
        # Group by category
        for category in results_df['category'].unique():
            cat_df = results_df[results_df['category'] == category]
            output['by_category'][category] = {
                'avg_score': round(cat_df['flow_score'].mean(), 1),
                'etf_count': len(cat_df),
                'top_etf': cat_df.iloc[0]['ticker'] if not cat_df.empty else None
            }
        
        # Save JSON
        with open(self.output_json, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved analysis to {self.output_json}")
        
        # Print summary
        logger.info("\n📊 ETF Flow Summary:")
        logger.info("Top 5 Inflows:")
        for _, row in results_df.head(5).iterrows():
            logger.info(f"   {row['ticker']}: Score {row['flow_score']} ({row['flow_signal']})")
        
        logger.info("\nTop 5 Outflows:")
        for _, row in results_df.tail(5).iterrows():
            logger.info(f"   {row['ticker']}: Score {row['flow_score']} ({row['flow_signal']})")
        
        return results_df


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ETF Flow Analysis')
    parser.add_argument('--dir', default='./data', help='Data directory')
    args = parser.parse_args()
    
    analyzer = ETFFlowAnalyzer(data_dir=args.dir)
    analyzer.run()


if __name__ == "__main__":
    main()
