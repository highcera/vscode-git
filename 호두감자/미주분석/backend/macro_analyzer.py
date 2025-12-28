#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Macro Market Analyzer - Collects macro indicators and generates AI insights
"""

import os, json, requests, logging
import yfinance as yf
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MacroDataCollector:
    def __init__(self):
        # Expanded tickers to match frontend
        self.macro_tickers = {
            '10Y_Yield': '^TNX', '2Y_Yield': '^IRX', '30Y_Yield': '^TYX',
            'BTC': 'BTC-USD', 'ETH': 'ETH-USD',
            'COPPER': 'HG=F', 'GOLD': 'GC=F', 'OIL': 'CL=F', 'NAT_GAS': 'NG=F',
            'DXY': 'DX-Y.NYB', 'EUR/USD': 'EURUSD=X', 'USD/KRW': 'KRW=X',
            'VIX': '^VIX', 'SKEW': '^SKEW',
            'SPY': 'SPY', 'QQQ': 'QQQ', 'IWM': 'IWM'
        }
    
    def get_current_macro_data(self) -> Dict:
        logger.info("📊 Fetching macro data...")
        macro_data = {}
        try:
            tickers = list(self.macro_tickers.values())
            data = yf.download(tickers, period='5d', progress=False)
            
            for name, ticker in self.macro_tickers.items():
                try:
                    if ticker not in data['Close'].columns: continue
                    hist = data['Close'][ticker].dropna()
                    if len(hist) < 2: continue
                    
                    val = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    change = ((val / prev) - 1) * 100
                    
                    macro_data[name] = {
                        'value': round(val, 2),
                        'change_1d': round(change, 2)
                    }
                except: pass
            
            # Yield Spread
            if '10Y_Yield' in macro_data and '2Y_Yield' in macro_data:
                spread = macro_data['10Y_Yield']['value'] - macro_data['2Y_Yield']['value']
                macro_data['YieldSpread'] = {'value': round(spread, 2), 'change_1d': 0}
            
        except Exception as e:
            logger.error(f"Error: {e}")
        return macro_data

    def get_macro_news(self) -> List[Dict]:
        news = []
        try:
            import xml.etree.ElementTree as ET
            url = "https://news.google.com/rss/search?q=Global+Macro+Economy+Fed+Rates&hl=en-US"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[:5]:
                    news.append({'title': item.find('title').text})
        except: pass
        return news


class MacroAIAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    def generate_content(self, prompt: str) -> str:
        if not self.api_key: return "API Key Missing - Check backend/.env"
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7}}
            resp = requests.post(f"{self.url}?key={self.api_key}", json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"Error: {e}"
        return "Analysis failed"

    def analyze_standard(self, data: Dict, news: List) -> str:
        metrics = "\n".join([f"- {k}: {v['value']} ({v.get('change_1d',0):+.2f}%)" for k,v in data.items()])
        headlines = "\n".join([n['title'] for n in news[:3]])
        
        prompt = f"""Role: Global Macro Strategist.
Data:
{metrics}
News:
{headlines}

Task: Write a market summary with investment advice.
Format:
## 1) Market Pulse
(Summary of current situation)
## 2) Key Opportunities & Risks
- **Opportunity**: ...
- **Risk**: ...
## 3) Strategy
(Asset allocation suggestion)

Language: Korean."""
        return self.generate_content(prompt)

    def analyze_historical(self, data: Dict, news: List) -> str:
        metrics = "\n".join([f"- {k}: {v['value']}" for k,v in data.items()])
        
        prompt = f"""Role: Quantitative Trend Researcher.
Data:
{metrics}

Task: Analyze the current market regime and compare it to historical patterns.
Focus on Yield Curve, VIX, and major assets.

Format:
## 1) Current Regime Analysis
- Yield Curve: (Steepening/Flattening) -> Implications
- Volatility: VIX Level -> Sentiment
- Liquidity: DXY/Gold -> Flow

## 2) Historical Pattern Matching
- **Most Similar Period**: (e.g., 2019 Rate Cut, 1995 Soft Landing, 2022 Inflation Shock)
- **Key Similarity**: Why is it similar?
- **What Happened Next**: How did assets perform then?

Language: Korean."""
        return self.generate_content(prompt)


class MultiModelAnalyzer:
    def __init__(self, data_dir='./data'):
        # Fix path to match typical backend structure
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.collector = MacroDataCollector()
        self.gemini = MacroAIAnalyzer()
    
    def run(self):
        logger.info("🚀 Starting Macro Analysis...")
        data = self.collector.get_current_macro_data()
        news = self.collector.get_macro_news()
        
        logger.info("🤖 Generating Gemini Insight...")
        analysis_std = self.gemini.analyze_standard(data, news)
        
        logger.info("🧠 Generating Historical Analysis (GPT Persona)...")
        analysis_hist = self.gemini.analyze_historical(data, news)
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'macro_indicators': data,
            'news': news,
            'overall_summary': analysis_std, # Legacy fallback
            'ai_analysis_gemini': analysis_std,
            'ai_analysis_gpt': analysis_hist
        }
        
        output_file = os.path.join(self.data_dir, 'macro_analysis.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {output_file}")
        
        # Simple logging
        for name, vals in data.items():
            logger.info(f"   {name}: {vals['value']}")

if __name__ == "__main__":
    MultiModelAnalyzer().run()
