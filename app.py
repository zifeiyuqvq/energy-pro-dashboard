from flask import Flask, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# 核心智能爬虫（加入了深度伪装）
def scrape_guojiyoujia(url, cid, name, exchange, unit, backup_symbol=None):
    # 深度伪装：模拟真实的 Windows Chrome 浏览器，加入多个迷惑性请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.baidu.com/"
    }
    
    data = {
        'id': cid, 'code': cid, 'name': name,
        'exchange': exchange, 'unit': unit,
        'price': '--', 'change': '--', 'changePct': '--',
        'high': '--', 'low': '--'
    }
    
    success = False
    
    try:
        # 尝试去国际油价网抓取
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(separator=' ')
            
            # 兼容多种美元符号的写法
            match_price = re.search(r'(?:US)?\$\s*([0-9\.,]+)', text)
            match_yest = re.search(r'昨日收盘\s*:\s*([0-9\.,]+)', text)
            match_high = re.search(r'今日最高\s*:\s*([0-9\.,]+)', text)
            match_low = re.search(r'今日最低\s*:\s*([0-9\.,]+)', text)
            
            if match_price:
                current_price = float(match_price.group(1).replace(',', ''))
                data['price'] = f"{current_price:.2f}"
                success = True
                
                if match_yest:
                    yest_price = float(match_yest.group(1).replace(',', ''))
                    if yest_price != 0:
                        change = current_price - yest_price
                        pct = (change / yest_price) * 100
                        data['change'] = f"{change:+.2f}"
                        data['changePct'] = f"{pct:+.2f}"
                
                if match_high: data['high'] = match_high.group(1).replace(',', '')
                if match_low: data['low'] = match_low.group(1).replace(',', '')
    except Exception as e:
        print(f"[{name}] 爬虫遇到障碍: {e}")

    # ===== 终极兜底机制 =====
    # 如果对方防火墙实在太严密抓取失败了，且我们有雅虎财经的备用代码，瞬间用雅虎数据兜底顶上！
    if not success and backup_symbol:
        try:
            ticker = yf.Ticker(backup_symbol)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[0]
                curr_price = hist['Close'].iloc[1]
                data['price'] = f"{curr_price:.2f}"
                change_val = curr_price - prev_close
                pct_val = (change_val / prev_close) * 100
                data['change'] = f"{change_val:+.2f}"
                data['changePct'] = f"{pct_val:+.2f}"
                data['high'] = f"{hist['High'].iloc[1]:.2f}"
                data['low'] = f"{hist['Low'].iloc[1]:.2f}"
        except:
            pass
            
    return data

@app.route('/api/data')
def get_market_data():
    # 目标网址，加上了 yfinance 的备用代码（防止网页上变成难看的 --）
    targets = [
        ("https://www.guojiyoujia.com/ICE_Low_Sulphur_Gasoil/", "gasoil", "ICE 国际柴油", "ICE", "USD/吨", None), 
        ("https://www.guojiyoujia.com/Brent/", "brent", "布伦特原油", "ICE", "USD/桶", "BZ=F"),
        ("https://www.guojiyoujia.com/", "wti", "WTI 纽约原油", "NYMEX", "USD/桶", "CL=F"),
        ("https://www.guojiyoujia.com/Dubai/", "dubai", "中东迪拜原油", "DME", "USD/桶", None),
        ("https://www.guojiyoujia.com/Natural_Gas/", "ngas", "NYMEX 天然气", "NYMEX", "USD/百万英热", "NG=F")
    ]
    
    market_data = []
    for url, cid, name, exchange, unit, backup in targets:
        market_data.append(scrape_guojiyoujia(url, cid, name, exchange, unit, backup))
        
    return jsonify(market_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
