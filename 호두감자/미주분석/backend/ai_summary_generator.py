#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Stock Summary Generator - Generates investment summaries using Gemini AI
"""

import os, json, logging, time, requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCollector:
    def get_news(self, ticker: str) -> list:
        try:
            import xml.etree.ElementTree as ET
            url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                return [{'title': item.find('title').text} for item in root.findall('.//item')[:3]]
        except: pass
        return []


class GeminiGenerator:
    def __init__(self):
        self.key = os.getenv('GOOGLE_API_KEY')
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
    def generate(self, ticker: str, data: dict, news: list, lang='ko') -> str:
        if not self.key: return "No API Key"
        
        news_txt = "\n".join([n['title'] for n in news]) if news else "No recent news"
        score_info = f"Score: {data.get('composite_score', 'N/A')}/100, Grade: {data.get('grade', 'N/A')}"
        
        prompt = f"""종목: {ticker}
정보: {score_info}
뉴스: {news_txt}
요청: 3-4문장으로 투자 의견 요약 (수급, 펀더멘털, 전략). 이모지 없이.""" if lang == 'ko' else f"""Stock: {ticker}
Info: {score_info}
News: {news_txt}
Request: 3-4 sentence investment summary. No emojis."""

        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = requests.post(f"{self.url}?key={self.key}", json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()['candidates'][0]['content']['parts'][0]['text']
        except: pass
        return "Analysis Failed"


class AIStockAnalyzer:
    def __init__(self, data_dir='./data'):
        self.data_dir = data_dir
        self.output = os.path.join(data_dir, 'ai_summaries.json')
        self.gen = GeminiGenerator()
        self.news = NewsCollector()
        
    def run(self, top_n=20):
        logger.info("🚀 Starting AI Summary Generator...")
        
        csv = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
        if not os.path.exists(csv):
            logger.error(f"❌ {csv} not found. Run smart_money_screener_v2.py first.")
            return
        
        df = pd.read_csv(csv).head(top_n)
        results = {}
        
        # Load existing
        if os.path.exists(self.output):
            with open(self.output) as f: 
                results = json.load(f)
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Generating summaries"):
            ticker = row['ticker']
            if ticker in results:
                # Check if previous run failed due to missing key
                prev_summary = results[ticker].get('summary', '')
                if 'No API Key' not in prev_summary:
                    continue
            
            news = self.news.get_news(ticker)
            summary_ko = self.gen.generate(ticker, row.to_dict(), news, 'ko')
            summary_en = self.gen.generate(ticker, row.to_dict(), news, 'en')
            
            results[ticker] = {
                'summary': summary_ko,
                'summary_ko': summary_ko,
                'summary_en': summary_en,
                'updated': datetime.now().isoformat()
            }
            time.sleep(1)  # Rate limit
        
        with open(self.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Saved {len(results)} summaries to {self.output}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--top', type=int, default=20)
    args = parser.parse_args()
    AIStockAnalyzer().run(top_n=args.top)
