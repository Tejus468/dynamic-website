import requests
from bs4 import BeautifulSoup
import sqlite3
import time

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
        cur.execute('CREATE TABLE IF NOT EXISTS prices (name TEXT, price TEXT, change_24h TEXT)')
        cur.execute('DELETE FROM prices')

        # Find the cryptocurrency table rows
        rows = soup.find_all('tr')
        count = 0
        
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 5:
                try:
                    # Extract coin name, price, and change
                    name_elem = columns[2].find('p')
                    price_elem = columns[3].find('span')
                    change_elem = columns[4].find('span')
                    
                    if name_elem and price_elem and change_elem:
                        name = name_elem.text.strip()
                        price = price_elem.text.strip()
                        change = change_elem.text.strip()
                        
                        # Clean the data
                        if price.startswith('$'):
                            price = price[1:]
                        
                        cur.execute("INSERT INTO prices VALUES (?, ?, ?)", (name, price, change))
                        count += 1
                        
                        if count >= 10:  # Get top 10 coins
                            break
                except Exception as e:
                    continue

        conn.commit()
        conn.close()
        print(f"Successfully scraped {count} coins")
        
    except Exception as e:
        print(f"Error scraping data: {e}")

if __name__ == '__main__':
    scrape_crypto()
