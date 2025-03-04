import  requests
from bs4 import BeautifulSoup
import mysql.connector
import time

# MySQL Configuration 
DB_CONFIG = {
    "host": "mysql_container_v2",  
    "user": "root",
    "password": "rootpassword",
    "database": "scrapper_db"
}

# Function to wait for MySQL to start
def wait_for_db(max_retries=10, delay=3):
    retries = 0
    while retries < max_retries:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            conn.close()
            print(" Connected to MySQL!")
            return
        except mysql.connector.Error as e:
            retries += 1
            print(f" Waiting for MySQL... {max_retries - retries} attempts left. Error: {e}")
            time.sleep(delay)
    raise Exception(" Could not connect to MySQL after multiple attempts.")

# Ensure table exists
def setup_database():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            text TEXT NOT NULL,
            author VARCHAR(255) NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print(" Database setup completed!")

# Function to scrape quotes
def scrape_quotes():
    URL = "https://quotes.toscrape.com/"
    
    for _ in range(3):  
        try:
            response = requests.get(URL, timeout=10)
            if response.status_code == 200:
                break
        except requests.RequestException as e:
            print(f" Request failed: {e}. Retrying...")
            time.sleep(3)
    else:
        print(" Failed to fetch webpage after multiple attempts.")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    quotes = []

    for quote in soup.find_all("div", class_="quote"):
        text = quote.find("span", class_="text").text.strip()
        author = quote.find("small", class_="author").text.strip()
        quotes.append((text, author))

    print(f" Scraped {len(quotes)} quotes.")
    return quotes

# Function to save quotes to MySQL
def save_to_db(quotes):
    if not quotes:
        print(" No data to save.")
        return
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.executemany("INSERT INTO quotes (text, author) VALUES (%s, %s)", quotes)
        conn.commit()
        
        print(f" Saved {cursor.rowcount} quotes to MySQL.")
        
    except mysql.connector.Error as e:
        print(f" Database error: {e}")
    
    finally:
        cursor.close()
        conn.close()

# Main Execution
if __name__ == "__main__":
    wait_for_db()
    setup_database()
    quotes = scrape_quotes()
    save_to_db(quotes)
