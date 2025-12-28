import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, render_template, jsonify, request
import traceback
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
# Path to backend data directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'backend', 'data')

print(f"Server started. Data directory: {BACKEND_DATA_DIR}")

# --- Sector Mapping ---
SECTOR_MAP = {
    'AAPL': 'Tech', 'MSFT': 'Tech', 'NVDA': 'Tech', 'AVGO': 'Tech', 
    'AMZN': 'Cons', 'TSLA': 'Cons', 'GOOGL': 'Comm', 'META': 'Comm',
    'JPM': 'Fin', 'V': 'Fin', 'UNH': 'Health', 'JNJ': 'Health',
    'XOM': 'Energy', 'CVX': 'Energy', 'PG': 'Staple', 'COST': 'Staple'
}

# --- Helper Functions ---

def get_data_path(filename):
    return os.path.join(BACKEND_DATA_DIR, filename)

def load_json(filename):
    path = get_data_path(filename)
    if not os.path.exists(path):
        print(f"File not found: {path} (Base: {BACKEND_DATA_DIR})")
        return {}
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        try:
            # Fallback for Windows CP949
            with open(path, 'r', encoding='cp949') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename} with cp949: {e}")
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return {}

def load_csv(filename):
    try:
        path = get_data_path(filename)
        if os.path.exists(path):
            return pd.read_csv(path)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return pd.DataFrame()

def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/us/smart-money')
def get_us_smart_money():
    """Get Top Picks from Smart Money Screener (PART2)"""
    try:
        # Load dashboard data first (if available)
        data = load_json('smart_money_current.json')
        if data and 'picks' in data:
            return jsonify({
                'analysis_date': datetime.now().strftime('%Y-%m-%d'), 
                'top_picks': data['picks'],
                'summary': {'total': len(data['picks'])}
            })

        # Fallback to CSV
        df = load_csv('smart_money_picks_v2.csv')
        if df.empty:
            return jsonify({'error': 'No data'}), 404
        
        # Determine AI recommendation logic if missing
        picks = []
        for _, row in df.head(50).iterrows():
            comp_score = row.get('composite_score', 0)
            rec = "Hold"
            if comp_score >= 80: rec = "Strong Buy"
            elif comp_score >= 60: rec = "Buy"
            elif comp_score <= 40: rec = "Sell"
            
            picks.append({
                'rank': row.get('rank', 0),
                'ticker': row['ticker'],
                'name': row.get('name', row['ticker']),
                'sector': row.get('sector', 'N/A'),
                'final_score': round(comp_score, 1),
                'ai_recommendation': rec,
                'current_price': row.get('current_price', 0),
                'target_upside': row.get('target_upside', 0),
                'price_at_rec': row.get('current_price', 0), # Simplified
                'change_since_rec': 0
            })
            
        return jsonify({
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'top_picks': picks,
            'summary': {'total_analyzed': len(df)}
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/etf-flows')
def get_us_etf_flows():
    """Get ETF Flows (PART1)"""
    try:
        df = load_csv('us_etf_flows.csv')
        ai_data = load_json('etf_flow_analysis.json')
        
        inflows = []
        outflows = []
        
        if not df.empty:
            # Sort by Flow Score
            if 'flow_score' in df.columns:
                df['flow_val'] = df['flow_score']
                inflows = df.nlargest(5, 'flow_val').to_dict('records')
                outflows = df.nsmallest(5, 'flow_val').to_dict('records')
        
        return jsonify({
            'inflows': inflows,
            'outflows': outflows,
            'ai_analysis': ai_data.get('analysis', "AI analysis not available."),
            'sentiment': ai_data.get('sentiment', 'Neutral')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/options-flow')
def get_us_options_flow():
    """Get Options Flow (PART2)"""
    try:
        data = load_json('options_flow.json')
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/market-map')
def get_us_market_map():
    """Get Market Map (Sector Heatmap)"""
    try:
        data = load_json('sector_heatmap.json')
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/macro-analysis')
def get_us_macro_analysis():
    """Get Macro Analysis (PART3) with Real-time Data"""
    try:
        # Load summary from JSON if available (for AI text)
        json_data = load_json('macro_analysis.json')
        
        # Define extended tickers based on user image
        tickers_map = {
            '10Y_Yield': '^TNX', '2Y_Yield': '^IRX', '30Y_Yield': '^TYX',
            'BTC': 'BTC-USD', 'ETH': 'ETH-USD',
            'COPPER': 'HG=F', 'GOLD': 'GC=F', 'SILVER': 'SI=F', 'OIL': 'CL=F', 'NAT_GAS': 'NG=F',
            'DXY': 'DX-Y.NYB', 'EUR/USD': 'EURUSD=X', 'USD/JPY': 'JPY=X', 'USD/KRW': 'KRW=X',
            'VIX': '^VIX', 'SKEW': '^SKEW',
            'SPY': 'SPY', 'QQQ': 'QQQ', 'DIA': 'DIA', 'IWM': 'IWM',
            'HY_Credit': 'HYG', 'IG_Credit': 'LQD',
            'VNQ': 'VNQ', 'XLE': 'XLE', 'XLF': 'XLF', 'XLK': 'XLK', 'XLU': 'XLU', 'XHB': 'XHB',
            'DAX': '^GDAXI', 'FTSE': '^FTSE', 'KOSPI': '^KS11', 'NIKKEI': '^N225', 'CSI300': '000300.SS',
            'YieldSpread': '10-2' # Special case
        }
        
        # Batch fetch
        symbols = [v for k, v in tickers_map.items() if v != '10-2']
        data = yf.download(symbols, period="5d", progress=False)['Close']
        
        indicators = {}
        
        # Helper to get change
        def get_vals(symbol):
            if symbol not in data.columns: return 0, 0
            series = data[symbol].dropna()
            if len(series) < 2: return series.iloc[-1] if not series.empty else 0, 0
            curr = series.iloc[-1]
            prev = series.iloc[-2]
            return curr, ((curr - prev) / prev) * 100

        for name, symbol in tickers_map.items():
            if name == 'YieldSpread':
                # Calc 10Y - 2Y
                t10, _ = get_vals('^TNX')
                t2, _ = get_vals('^IRX')
                val = t10 - t2
                # Calculate change of spread? roughly
                prev_t10 = data['^TNX'].dropna().iloc[-2] if len(data['^TNX'].dropna()) > 1 else t10
                prev_t2 = data['^IRX'].dropna().iloc[-2] if len(data['^IRX'].dropna()) > 1 else t2
                prev_val = prev_t10 - prev_t2
                change = val - prev_val # Point change
                indicators[name] = {"value": round(val, 2), "change": round(change, 2), "is_spread": True}
            else:
                val, change = get_vals(symbol)
                indicators[name] = {"value": round(val, 2), "change": round(change, 2)}

        return jsonify({
            "macro_indicators": indicators,
            "overall_summary": json_data.get("overall_summary", "Real-time macro data loaded.")
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/ai-summary/<ticker>')
def get_us_ai_summary(ticker):
    """Get AI Summary for a specific ticker (PART3)"""
    try:
        data = load_json('ai_summaries.json')
        summary = data.get(ticker, {})
        lang = request.args.get('lang', 'ko')
        
        text = summary.get('summary_ko' if lang == 'ko' else 'summary_en', '')
        if not text:
            text = summary.get('summary', 'No summary available.')
            
        return jsonify({'summary': text, 'updated': summary.get('updated', '')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/portfolio')
def get_us_market_indices():
    """Get US Market Indices (Real-time via yfinance)"""
    try:
        indices = {
            '^DJI': 'Dow Jones', '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ',
            '^RUT': 'Russell 2000', '^VIX': 'VIX', 'GC=F': 'Gold',
            'CL=F': 'Crude Oil', 'BTC-USD': 'Bitcoin', '^TNX': '10Y Treasury',
            'DX-Y.NYB': 'Dollar Index', 'KRW=X': 'USD/KRW'
        }
        
        data = []
        # Optimization: Fetch all at once if possible, or use Threading
        # For simplicity here, sequential (can be slow) or yf.download
        
        tickers = list(indices.keys())
        hist_data = yf.download(tickers, period='5d', progress=False)
        
        closes = hist_data['Close']
        
        for tik, name in indices.items():
            try:
                if tik in closes.columns:
                    series = closes[tik].dropna()
                else:
                    # Fallback for single ticker download structure or missing data
                    continue
                    
                if len(series) >= 2:
                    curr = series.iloc[-1]
                    prev = series.iloc[-2]
                    change = curr - prev
                    pct = (change / prev) * 100
                    
                    data.append({
                        'name': name,
                        'price': f"{curr:,.2f}",
                        'change': f"{change:+,.2f}",
                        'change_pct': round(pct, 2),
                        'color': 'green' if change >= 0 else 'red'
                    })
            except: pass
            
        return jsonify({'market_indices': data})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/stock-chart/<ticker>')
def get_stock_chart(ticker):
    """Get Chart Data"""
    try:
        period = request.args.get('period', '1y')
        interval = '1d'
        if period in ['1d', '5d']: interval = '5m' if period == '1d' else '15m'
        elif period in ['1mo', '3mo']: interval = '1d'
        
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            return jsonify({'error': 'No data'}), 404
            
        # Format for Lightweight Charts
        data = []
        for idx, row in hist.iterrows():
            data.append({
                'time': idx.strftime('%Y-%m-%d') if interval == '1d' else int(idx.timestamp()),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume']
            })
            
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/technical-indicators/<ticker>')
def get_technical_indicators(ticker):
    """Get RSI, MACD, BB"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='1y')
        
        close = hist['Close']
        
        # RSI
        rsi = calculate_rsi(close)
        
        # MACD
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # BB
        ma20 = close.rolling(window=20).mean()
        std = close.rolling(window=20).std()
        upper = ma20 + (std * 2)
        lower = ma20 - (std * 2)
        
        # Format (Last 100 points to reduce size)
        limit = 200
        dates = hist.index[-limit:]
        
        result = {
            'rsi': [{'time': d.strftime('%Y-%m-%d'), 'value': v} for d, v in zip(dates, rsi[-limit:])],
            'macd': [{'time': d.strftime('%Y-%m-%d'), 'macd': m, 'signal': s, 'hist': m-s} for d, m, s in zip(dates, macd[-limit:], signal[-limit:])],
            'bb': [{'time': d.strftime('%Y-%m-%d'), 'upper': u, 'lower': l, 'middle': m} for d, u, l, m in zip(dates, upper[-limit:], lower[-limit:], ma20[-limit:])]
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/history-dates')
def get_history_dates():
    # Only for demonstration
    return jsonify({'dates': [datetime.now().strftime('%Y-%m-%d')]})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
