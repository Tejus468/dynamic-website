from flask import Flask, render_template, redirect, url_for
import sqlite3
from scraper import scrape_crypto
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

@app.route('/')
def index():
    conn = sqlite3.connect('crypto.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM prices')
    data = cur.fetchall()
    conn.close()
    return render_template('index.html', data=data)

@app.route('/refresh')
def refresh():
    scrape_crypto()
    return redirect(url_for('index'))  # Redirect back to main page

# Setup automatic scraping every 10 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_crypto, trigger="interval", minutes=10)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # Initial scrape when starting the app
    scrape_crypto()
    app.run(debug=True, host='0.0.0.0', port=5000)
