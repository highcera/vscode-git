#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Economic Calendar - Fetches economic events with AI impact analysis
"""

import os, json, requests, logging
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EconomicCalendar:
    def __init__(self, data_dir='./data'):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.output = os.path.join(data_dir, 'weekly_calendar.json')
        
    def get_events(self) -> list:
        events = []
        
        # Add major known events
        base_events = [
            {'event': 'FOMC Meeting Minutes', 'impact': 'High'},
            {'event': 'Nonfarm Payrolls', 'impact': 'High'},
            {'event': 'CPI Report', 'impact': 'High'},
            {'event': 'Initial Jobless Claims', 'impact': 'Medium'},
            {'event': 'Retail Sales', 'impact': 'Medium'},
            {'event': 'GDP Report', 'impact': 'High'},
        ]
        
        # Try Yahoo Finance Calendar
        try:
            url = "https://finance.yahoo.com/calendar/economic"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                dfs = pd.read_html(StringIO(resp.text))
                if dfs:
                    df = dfs[0]
                    if 'Country' in df.columns:
                        us = df[df['Country'] == 'US']
                        for _, row in us.head(10).iterrows():
                            events.append({
                                'date': datetime.now().strftime('%Y-%m-%d'),
                                'event': str(row.get('Event', 'Unknown')),
                                'impact': 'Medium',
                                'actual': str(row.get('Actual', '-')),
                                'estimate': str(row.get('Market Expectation', '-'))
                            })
        except Exception as e:
            logger.debug(f"Yahoo calendar fetch failed: {e}")
        
        # Add base events if none found
        if not events:
            today = datetime.now()
            for i, ev in enumerate(base_events):
                events.append({
                    'date': (today + timedelta(days=i)).strftime('%Y-%m-%d'),
                    'event': ev['event'],
                    'impact': ev['impact'],
                    'description': 'Scheduled economic release'
                })
        
        return events
    
    def enrich_ai(self, events: list) -> list:
        key = os.getenv('GOOGLE_API_KEY')
        if not key: return events
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        for ev in events:
            if ev.get('impact') == 'High':
                try:
                    prompt = f"2문장으로 '{ev['event']}'가 미국 주식 시장에 미치는 영향을 설명하세요."
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    resp = requests.post(f"{url}?key={key}", json=payload, timeout=15)
                    if resp.status_code == 200:
                        ai_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
                        ev['ai_insight'] = ai_text
                except: pass
        
        return events

    def run(self):
        logger.info("🚀 Fetching Economic Calendar...")
        
        events = self.get_events()
        events = self.enrich_ai(events)
        
        output = {
            'updated': datetime.now().isoformat(),
            'week_start': datetime.now().strftime('%Y-%m-%d'),
            'event_count': len(events),
            'events': events
        }
        
        with open(self.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {self.output}")
        
        # Print summary
        logger.info(f"\n📅 Upcoming Events: {len(events)}")
        for ev in events[:5]:
            icon = "🔴" if ev.get('impact') == 'High' else "🟡"
            logger.info(f"   {icon} {ev['event']}")

if __name__ == "__main__":
    EconomicCalendar().run()
