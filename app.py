from flask import Flask, render_template, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def get_market_data():
    targets = [
        {'id': 'gasoil', 'code': 'HO=F', 'name': '国际燃油(替代柴油)', 'exchange': 'NYMEX', 'unit': 'USD/加仑'},
        {'id': 'brent', 'code': 'BZ=F', 'name': '布伦特原油', 'exchange': 'ICE', 'unit': 'USD/桶'},
        {'id': 'wti', 'code': 'CL=F', 'name': 'WTI 纽约原油', 'exchange': 'NYMEX', 'unit': 'USD/桶'},
        {'id': 'dubai', 'code': 'OQD=F', 'name': '中东阿曼基准', 'exchange': 'DME', 'unit': 'USD/桶'},
        {'id': 'ngas', 'code': 'NG=F', 'name': 'NYMEX 天然气', 'exchange': 'NYMEX', 'unit': 'USD/百万英热'}
    ]
    
    market_data = []
    
    for item in targets:
        data = {
            'id': item['id'], 'code': item['code'], 'name': item['name'],
            'exchange': item['exchange'], 'unit': item['unit'],
            'price': '--', 'change': '--', 'changePct': '--',
            'high': '--', 'low': '--'
        }
        
        try:
            # 扩大到 5d，完美避开周末和节假日休市导致的“空数据”报错！
            ticker = yf.Ticker(item['code'])
            hist = ticker.history(period="5d")
            
            if len(hist) >= 2:
                # 拿最近的倒数第二天作为昨收，倒数第一天作为最新价
                prev_close = hist['Close'].iloc[-2]
                curr_price = hist['Close'].iloc[-1]
                
                change = curr_price - prev_close
                pct = (change / prev_close) * 100
                
                data['price'] = f"{curr_price:.2f}"
                data['change'] = f"{change:+.2f}"
                data['changePct'] = f"{pct:+.2f}"
                data['high'] = f"{hist['High'].iloc[-1]:.2f}"
                data['low'] = f"{hist['Low'].iloc[-1]:.2f}"
            elif len(hist) == 1:
                # 极端情况：只有一天的数据
                curr_price = hist['Close'].iloc[-1]
                data['price'] = f"{curr_price:.2f}"
                
        except Exception as e:
            # 即使某一个品种报错，也会打印出来，但绝不会让整个网页崩溃
            print(f"Error fetching {item['code']}: {e}")
            
        market_data.append(data)
        
    return jsonify(market_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
