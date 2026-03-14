from flask import Flask, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# 当访问网址时，展示你的炫酷 HTML
@app.route('/')
def home():
    return render_template('index.html')

# 核心智能爬虫函数：去指定网址抠出最新价格和涨跌幅
def scrape_guojiyoujia(url, cid, name, exchange, unit):
    # 伪装成真实的浏览器，防止被对方防火墙拦截
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # 默认空数据格式
    data = {
        'id': cid, 'code': cid, 'name': name,
        'exchange': exchange, 'unit': unit,
        'price': '--', 'change': '--', 'changePct': '--',
        'high': '--', 'low': '--'
    }
    
    try:
        # 发送请求并解析网页
        resp = requests.get(url, headers=headers, timeout=5)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 提取网页上所有的纯文本
        text = soup.get_text(separator=' ')
        
        # 使用正则表达式（Regex）精准匹配网页里的特殊字符
        match_price = re.search(r'\$\s*([0-9\.,]+)', text)
        match_yest = re.search(r'昨日收盘\s*:\s*([0-9\.,]+)', text)
        match_high = re.search(r'今日最高\s*:\s*([0-9\.,]+)', text)
        match_low = re.search(r'今日最低\s*:\s*([0-9\.,]+)', text)
        
        if match_price:
            current_price = float(match_price.group(1).replace(',', ''))
            data['price'] = f"{current_price:.2f}"
            
            # 如果能找到昨天的收盘价，Python 自动帮你算出涨跌幅！
            if match_yest:
                yest_price = float(match_yest.group(1).replace(',', ''))
                if yest_price != 0:
                    change = current_price - yest_price
                    pct = (change / yest_price) * 100
                    data['change'] = f"{change:+.2f}"
                    data['changePct'] = f"{pct:+.2f}"
            
            # 提取最高和最低价
            if match_high:
                data['high'] = match_high.group(1).replace(',', '')
            if match_low:
                data['low'] = match_low.group(1).replace(',', '')
                
    except Exception as e:
        print(f"抓取 {name} 失败: {e}")
        
    return data

# 你的专属数据接口：负责统筹 5 大品种的爬取
@app.route('/api/data')
def get_market_data():
    # 目标抓取网址列表 (全部精准指向 guojiyoujia.com 的各大子页面)
    targets = [
        ("https://www.guojiyoujia.com/ICE_Low_Sulphur_Gasoil/", "gasoil", "ICE 国际柴油", "ICE", "USD/吨"),
        ("https://www.guojiyoujia.com/Brent/", "brent", "布伦特原油", "ICE", "USD/桶"),
        ("https://www.guojiyoujia.com/", "wti", "WTI 纽约原油", "NYMEX", "USD/桶"), # 首页默认显示 WTI 主力
        ("https://www.guojiyoujia.com/Dubai/", "dubai", "中东迪拜原油", "DME", "USD/桶"),
        ("https://www.guojiyoujia.com/Natural_Gas/", "ngas", "NYMEX 天然气", "NYMEX", "USD/百万英热")
    ]
    
    market_data = []
    # 循环去各大页面抓取数据
    for url, cid, name, exchange, unit in targets:
        market_data.append(scrape_guojiyoujia(url, cid, name, exchange, unit))
        
    return jsonify(market_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
