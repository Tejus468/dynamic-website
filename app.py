from flask import Flask, render_template, redirect, url_for, flash, jsonify, request
import sqlite3
from scraper import scrape_crypto, scrape_crypto_news
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import json
from datetime import datetime, timedelta
import csv
import io

app = Flask(__name__)
app.secret_key = 'crypto-tracker-secret-key-2025'

@app.route('/')
def index():
    conn = sqlite3.connect('crypto.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM prices ORDER BY id DESC LIMIT 15')
    data = cur.fetchall()
    
    # Get market summary
    cur.execute('SELECT COUNT(*), AVG(price), SUM(CASE WHEN change_24h LIKE "+%" THEN 1 ELSE 0 END) FROM prices')
    market_stats = cur.fetchone()
    
    # Get news
    cur.execute('SELECT * FROM news ORDER BY timestamp DESC LIMIT 5')
    news_data = cur.fetchall()
    
    conn.close()
    
    return render_template('index.html', data=data, market_stats=market_stats, news=news_data)

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('crypto.db')
    cur = conn.cursor()
    
    # Get top performers
    cur.execute("""SELECT name, price, change_24h FROM prices 
                   WHERE change_24h NOT LIKE '-%' 
                   ORDER BY CAST(REPLACE(change_24h, '%', '') AS REAL) DESC LIMIT 5""")
    top_gainers = cur.fetchall()
    
    cur.execute("""SELECT name, price, change_24h FROM prices 
                   WHERE change_24h LIKE '-%' 
                   ORDER BY CAST(REPLACE(REPLACE(change_24h, '-', ''), '%', '') AS REAL) DESC LIMIT 5""")
    top_losers = cur.fetchall()
    
    # Get historical data for charts
    cur.execute("""SELECT name, price, timestamp FROM prices 
                   WHERE timestamp > datetime('now', '-24 hours') 
                   ORDER BY timestamp DESC""")
    historical_data = cur.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         top_gainers=top_gainers, 
                         top_losers=top_losers,
                         historical_data=historical_data)

@app.route('/portfolio')
def portfolio():
    conn = sqlite3.connect('crypto.db')
    cur = conn.cursor()
    
    # Get portfolio data with current prices
    cur.execute("""
        SELECT p.*, pr.price as current_price 
        FROM portfolio p 
        LEFT JOIN prices pr ON p.coin_name = pr.name 
        ORDER BY p.buy_date DESC
    """)
    portfolio_data = cur.fetchall()
    
    # Calculate portfolio value
    total_value = 0
    total_invested = 0
    for item in portfolio_data:
        if item[7]:  # current_price exists
            current_value = item[3] * item[7]  # quantity * current_price
            invested = item[3] * item[4]  # quantity * buy_price
            total_value += current_value
            total_invested += invested
    
    profit_loss = total_value - total_invested
    
    conn.close()
    
    return render_template('portfolio.html', 
                         portfolio=portfolio_data,
                         total_value=total_value,
                         total_invested=total_invested,
                         profit_loss=profit_loss)

@app.route('/add_to_portfolio', methods=['POST'])
def add_to_portfolio():
    coin_name = request.form['coin_name']
    symbol = request.form['symbol']
    quantity = float(request.form['quantity'])
    buy_price = float(request.form['buy_price'])
    
    conn = sqlite3.connect('crypto.db')
    cur = conn.cursor()
    cur.execute("""INSERT INTO portfolio (coin_name, symbol, quantity, buy_price) 
                   VALUES (?, ?, ?, ?)""", (coin_name, symbol, quantity, buy_price))
    conn.commit()
    conn.close()
    
    flash(f'Added {quantity} {coin_name} to portfolio!', 'success')
    return redirect(url_for('portfolio'))

@app.route('/set_alert', methods=['POST'])
def set_alert():
    coin_name = request.form['coin_name']
    target_price = float(request.form['target_price'])
    alert_type = request.form['alert_type']
    
    conn = sqlite3.connect('crypto.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO alerts (coin_name, target_price, alert_type) VALUES (?, ?, ?)", 
                (coin_name, target_price, alert_type))
    conn.commit()
    conn.close()
    
    flash(f'Alert set for {coin_name} at ${target_price}!', 'success')
    return redirect(url_for('index'))

@app.route('/api/coin/<coin_name>')
def api_coin_details(coin_name):
    conn = sqlite3.connect('crypto.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM prices WHERE name = ? ORDER BY timestamp DESC LIMIT 1', (coin_name,))
    coin_data = cur.fetchone()
    
    # Get historical prices for chart
    cur.execute('SELECT price, timestamp FROM prices WHERE name = ? ORDER BY timestamp DESC LIMIT 24', (coin_name,))
    price_history = cur.fetchall()
    
    conn.close()
    
    if coin_data:
        coin_dict = {
            'name': coin_data[1],
            'symbol': coin_data[2],
            'price': coin_data[3],
            'change_24h': coin_data[4],
            'change_7d': coin_data[5],
            'market_cap': coin_data[6],
            'volume_24h': coin_data[7],
            'price_history': price_history
        }
        return jsonify(coin_dict)
    else:
        return jsonify({'error': 'Coin not found'}), 404

@app.route('/api/market_data')
def api_market_data():
    conn = sqlite3.connect('crypto.db')
    cur = conn.cursor()
    
    # Get market overview data
    cur.execute("""SELECT 
                   COUNT(*) as total_coins,
                   SUM(CAST(REPLACE(REPLACE(market_cap, '$', ''), 'B', '') AS REAL)) as total_market_cap,
                   AVG(price) as avg_price
                   FROM prices WHERE market_cap != 'N/A'""")
    market_data = cur.fetchone()
    
    cur.execute('SELECT name, price FROM prices ORDER BY price DESC LIMIT 10')
    top_coins = cur.fetchall()
    
    conn.close()
    
    return jsonify({
        'market_overview': market_data,
        'top_coins': top_coins
    })

@app.route('/export_csv')
def export_csv():
    conn = sqlite3.connect('crypto.db')
    cur = conn.cursor()
    cur.execute('SELECT name, symbol, price, change_24h, market_cap, volume_24h FROM prices')
    data = cur.fetchall()
    conn.close()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Symbol', 'Price', '24h Change', 'Market Cap', 'Volume'])
    writer.writerows(data)
    
    # Return as downloadable file
    response = app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=crypto_data.csv'}
    )
    return response

@app.route('/refresh')
def refresh():
    try:
        scrape_crypto()
        scrape_crypto_news()
        flash('Data refreshed successfully!', 'success')
    except Exception as e:
        flash(f'Error refreshing data: {str(e)}', 'error')
    return redirect(url_for('index'))

# Auto-update every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_crypto, trigger="interval", minutes=5)
scheduler.add_job(func=scrape_crypto_news, trigger="interval", hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    scrape_crypto()
    scrape_crypto_news()
    app.run(debug=True, host='0.0.0.0', port=5000)
