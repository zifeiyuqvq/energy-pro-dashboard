from flask import Flask, render_template, jsonify
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

# 当用户访问你的网址时，返回那个漂亮的 HTML 网页
@app.route('/')
def home():
    return render_template('index.html')

# 你的专属 API 接口：负责去抓取全网真实数据
@app.route('/api/data')
def get_market_data():
    market_data = []
    
    # --- 1. 爬虫抓取 ICE 国际柴油 (guojiyoujia.com) ---
    gasoil_price, gasoil_change, gasoil_pct = "--", "--", "--"
    try:
        url = "https://www.guojiyoujia.com/ICE_Low_Sulphur_Gasoil/"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 寻找带 $ 符号的文本
        price_tag = soup.find(string=lambda t: t and '$' in t)
        if price_tag:
            gasoil_price = price_tag.replace('$', '').replace(',', '').strip()
    except Exception as e:
        pass # 如果目标网站卡顿，直接跳过，防止我们的网页崩溃

    market_data.append({
        'id': 'gasoil', 'code': 'ICE_GAS', 'name': 'ICE 国际柴油', 
        'exchange': 'ICE', 'unit': 'USD/吨', 'price': gasoil_price, 
        'change': gasoil_change, 'changePct': gasoil_pct, 'high': '--', 'low': '--'
    })

    # --- 2. 雅虎财经获取国际四大品种 ---
    yahoo_symbols = [
        {'id': 'brent', 'code': 'BZ=F', 'name': '布伦特原油', 'exchange': 'ICE', 'unit': 'USD/桶'},
        {'id': 'wti', 'code': 'CL=F', 'name': 'WTI 纽约原油', 'exchange': 'NYMEX', 'unit': 'USD/桶'},
        {'id': 'ngas', 'code': 'NG=F', 'name': 'NYMEX 天然气', 'exchange': 'NYMEX', 'unit': 'USD/百万英热'},
        {'id': 'gold', 'code': 'GC=F', 'name': 'COMEX 黄金', 'exchange': 'COMEX', 'unit': 'USD/盎司'}
    ]

    for item in yahoo_symbols:
        price, change, pct, high, low = "--", "--", "--", "--", "--"
        try:
            ticker = yf.Ticker(item['code'])
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[0]
                curr_price = hist['Close'].iloc[1]
                high_val = hist['High'].iloc[1]
                low_val = hist['Low'].iloc[1]
                
                change_val = curr_price - prev_close
                pct_val = (change_val / prev_close) * 100
                
                price = f"{curr_price:.2f}"
                change = f"{change_val:+.2f}"
                pct = f"{pct_val:+.2f}"
                high = f"{high_val:.2f}"
                low = f"{low_val:.2f}"
        except Exception:
            pass

        market_data.append({
            'id': item['id'], 'code': item['code'], 'name': item['name'], 
            'exchange': item['exchange'], 'unit': item['unit'], 'price': price, 
            'change': change, 'changePct': pct, 'high': high, 'low': low
        })

    return jsonify(market_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
