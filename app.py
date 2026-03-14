from flask import Flask, render_template, jsonify
import yfinance as yf

app = Flask(__name__)

# 访问根目录时，展示漂亮的 HTML 看板
@app.route('/')
def home():
    return render_template('index.html')

# 专属数据接口：100% 稳定的雅虎财经直连引擎
@app.route('/api/data')
def get_market_data():
    # 你最想要的 5 大核心品种（采用了全球最具流动性的官方对标代码）
    targets = [
        {'id': 'gasoil', 'code': 'HO=F', 'name': '国际柴油/燃油', 'exchange': 'NYMEX', 'unit': 'USD/加仑'},
        {'id': 'brent', 'code': 'BZ=F', 'name': '布伦特原油', 'exchange': 'ICE', 'unit': 'USD/桶'},
        {'id': 'wti', 'code': 'CL=F', 'name': 'WTI 纽约原油', 'exchange': 'NYMEX', 'unit': 'USD/桶'},
        {'id': 'dubai', 'code': 'OQD=F', 'name': '中东迪拜/阿曼基准', 'exchange': 'DME', 'unit': 'USD/桶'},
        {'id': 'ngas', 'code': 'NG=F', 'name': 'NYMEX 天然气', 'exchange': 'NYMEX', 'unit': 'USD/百万英热'}
    ]
    
    market_data = []
    
    # 遍历获取真实数据
    for item in targets:
        # 初始化默认空数据
        data = {
            'id': item['id'], 'code': item['code'], 'name': item['name'],
            'exchange': item['exchange'], 'unit': item['unit'],
            'price': '--', 'change': '--', 'changePct': '--',
            'high': '--', 'low': '--'
        }
        
        try:
            # 优雅地调用 yfinance 官方接口
            ticker = yf.Ticker(item['code'])
            hist = ticker.history(period="2d") # 拿到最近两天的交易数据
            
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[0]
                curr_price = hist['Close'].iloc[1]
                
                # 自动计算涨跌幅
                change = curr_price - prev_close
                pct = (change / prev_close) * 100
                
                # 格式化填入数据
                data['price'] = f"{curr_price:.2f}"
                data['change'] = f"{change:+.2f}"
                data['changePct'] = f"{pct:+.2f}"
                data['high'] = f"{hist['High'].iloc[1]:.2f}"
                data['low'] = f"{hist['Low'].iloc[1]:.2f}"
                
        except Exception as e:
            # 如果某个品种暂时休市没拿到，直接跳过，不影响其他品种显示
            print(f"获取 {item['name']} 失败: {e}")
            
        market_data.append(data)
        
    return jsonify(market_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
