import os
import json
from datetime import datetime
import urllib.parse
import psycopg2
from psycopg2.extras import DictCursor

class Storage:
    def __init__(self):
        self.conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        self.create_tables()

    def create_tables(self):
        with self.conn.cursor() as cur:
            # Settings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # URLs table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS monitored_urls (
                    url TEXT PRIMARY KEY
                )
            """)

            # Articles table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    content TEXT NOT NULL,
                    processed_date TIMESTAMP NOT NULL
                )
            """)

            # Newsletters table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS news_newsletters (
                    id SERIAL PRIMARY KEY,
                    date TIMESTAMP NOT NULL,
                    content TEXT NOT NULL,
                    articles JSONB NOT NULL
                )
            """)

            self.conn.commit()

    def get_setting(self, key, default=""):
        with self.conn.cursor() as cur:
            cur.execute("SELECT value FROM app_settings WHERE key = %s", (key,))
            result = cur.fetchone()
            return result[0] if result else default

    def save_setting(self, key, value):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO app_settings (key, value) 
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """, (key, value))
            self.conn.commit()

    def add_url(self, url):
        try:
            # Basic URL validation
            result = urllib.parse.urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False

            with self.conn.cursor() as cur:
                cur.execute("INSERT INTO monitored_urls (url) VALUES (%s) ON CONFLICT DO NOTHING", (url,))
                self.conn.commit()
                return True
        except:
            return False

    def remove_url(self, url):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM monitored_urls WHERE url = %s", (url,))
            self.conn.commit()

    def get_urls(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT url FROM monitored_urls")
            return [row[0] for row in cur.fetchall()]

    def save_article(self, article):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO news_articles (url, title, summary, content, processed_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                article['url'],
                article['title'],
                article['summary'],
                article['content'],
                article['processed_date']
            ))
            self.conn.commit()

    def get_recent_articles(self, limit=10):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT url, title, summary, processed_date 
                FROM news_articles 
                ORDER BY processed_date DESC 
                LIMIT %s
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]

    def save_newsletter(self, newsletter):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO news_newsletters (date, content, articles)
                VALUES (%s, %s, %s)
            """, (
                newsletter['date'],
                newsletter['content'],
                json.dumps(newsletter['articles'])
            ))
            self.conn.commit()

    def get_newsletters(self, search_term=None):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            if search_term:
                cur.execute("""
                    SELECT date, content, articles 
                    FROM news_newsletters 
                    WHERE content ILIKE %s 
                    ORDER BY date DESC
                """, (f'%{search_term}%',))
            else:
                cur.execute("""
                    SELECT date, content, articles 
                    FROM news_newsletters 
                    ORDER BY date DESC
                """)
            return [dict(row) for row in cur.fetchall()]

    def get_unprocessed_articles(self, since_date):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT * FROM news_articles 
                WHERE processed_date > %s 
                ORDER BY processed_date DESC
            """, (since_date,))
            return [dict(row) for row in cur.fetchall()]