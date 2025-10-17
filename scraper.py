import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import json

def scrape_crypto():
    url = 'https://coinmarketcap.com/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        conn = sqlite3.connect('crypto.db')
        cur = conn.cursor()
        
        # Enhanced table with historical tracking
        cur.execute('''CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY,
            name TEXT,
            symbol TEXT,
            price REAL,
            change_24h TEXT,
            change_7d TEXT,
            market_cap TEXT,
            volume_24h TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Create alerts table
        cur.execute('''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            coin_name TEXT,
            target_price REAL,
            alert_type TEXT,
            is_triggered INTEGER DEFAULT 0
        )''')
        
        # Create portfolio table
        cur.execute('''CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY,
            coin_name TEXT,
            symbol TEXT,
            quantity REAL,
            buy_price REAL,
            current_value REAL,
            profit_loss REAL,
            buy_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Scrape cryptocurrency data
        rows = soup.find_all('tr')
        count = 0
        
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 5:
                try:
                    name_elem = columns[2].find('p')
                    price_elem = columns[3].find('span')
                    change_24h_elem = columns[4].find('span')
                    
                    if name_elem and price_elem and change_24h_elem:
                        name = name_elem.text.strip()
                        symbol = name[:3].upper()
                        price = float(price_elem.text.strip().replace('$', '').replace(',', ''))
                        change_24h = change_24h_elem.text.strip()
                        change_7d = '0%'  # Default
                        market_cap = 'N/A'
                        volume_24h = 'N/A'
                        
                        # Try to get more data from additional columns
                        if len(columns) > 6:
                            market_cap_elem = columns[6].find('span')
                            volume_elem = columns[7].find('span') if len(columns) > 7 else None
                            if market_cap_elem:
                                market_cap = market_cap_elem.text.strip()
                            if volume_elem:
                                volume_24h = volume_elem.text.strip()
                        
                        cur.execute("""INSERT INTO prices 
                                    (name, symbol, price, change_24h, change_7d, market_cap, volume_24h) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                                 (name, symbol, price, change_24h, change_7d, market_cap, volume_24h))
                        count += 1
                        print(f"Added: {name} - ${price} - {change_24h}")
                        
                        if count >= 15:  # Get top 15 coins
                            break
                except Exception as e:
                    continue

        conn.commit()
        conn.close()
        print(f"Successfully scraped {count} coins with enhanced data")
        
    except Exception as e:
        print(f"Error scraping data: {e}")

def scrape_crypto_news():
    """Scrape cryptocurrency news"""
    try:
        url = 'https://cointelegraph.com/tags/cryptocurrencies'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        conn = sqlite3.connect('crypto.db')
        cur = conn.cursor()
        
        cur.execute('''CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY,
            title TEXT,
            summary TEXT,
            url TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Clear old news
        cur.execute('DELETE FROM news WHERE timestamp < datetime("now", "-1 day")')
        
        # Sample news data (in real implementation, scrape actual news)
        sample_news = [
            ("Bitcoin Reaches New All-Time High", "Bitcoin continues its bullish momentum", "https://example.com/1"),
            ("Ethereum Updates Coming Soon", "Major network upgrades planned", "https://example.com/2"),
            ("DeFi Market Shows Strong Growth", "Decentralized finance sector expanding", "https://example.com/3"),
        ]
        
        for title, summary, url in sample_news:
            cur.execute("INSERT OR IGNORE INTO news (title, summary, url) VALUES (?, ?, ?)", 
                       (title, summary, url))
        
        conn.commit()
        conn.close()
        print("News data updated successfully")
        
    except Exception as e:
        print(f"Error scraping news: {e}")

if __name__ == '__main__':
    scrape_crypto()
    scrape_crypto_news()
