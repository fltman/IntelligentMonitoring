import os
import json
from datetime import datetime
import urllib.parse
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor
from contextlib import contextmanager

class Storage:
    def __init__(self):
        self.pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=os.getenv('DATABASE_URL')
        )
        self.create_tables()

    @contextmanager
    def get_conn(self):
        """Get a database connection from the pool"""
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def create_tables(self):
        """Create database tables if they don't exist"""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
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
                        articles JSONB NOT NULL,
                        podcast_script JSONB
                    )
                """)

    def get_setting(self, key, default=""):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM app_settings WHERE key = %s", (key,))
                result = cur.fetchone()
                return result[0] if result else default

    def save_setting(self, key, value):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO app_settings (key, value) 
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """, (key, value))

    def add_url(self, url):
        try:
            # Basic URL validation
            result = urllib.parse.urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False

            with self.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO monitored_urls (url) VALUES (%s) ON CONFLICT DO NOTHING", (url,))
                    return True
        except:
            return False

    def remove_url(self, url):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM monitored_urls WHERE url = %s", (url,))

    def get_urls(self):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT url FROM monitored_urls")
                return [row[0] for row in cur.fetchall()]

    def save_article(self, article):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
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

    def get_recent_articles(self, limit=10):
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT url, title, summary, processed_date 
                    FROM news_articles 
                    ORDER BY processed_date DESC 
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]

    def save_newsletter(self, newsletter):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO news_newsletters (date, content, articles, podcast_script)
                    VALUES (%s, %s, %s, %s)
                """, (
                    newsletter['date'],
                    newsletter['content'],
                    json.dumps(newsletter['articles']),
                    json.dumps(newsletter.get('podcast_script')) if newsletter.get('podcast_script') else None
                ))

    def get_newsletters(self, search_term=None):
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                if search_term:
                    cur.execute("""
                        SELECT id, date, content, articles, podcast_script, audio_url
                        FROM news_newsletters 
                        WHERE content ILIKE %s 
                        ORDER BY date DESC
                    """, (f'%{search_term}%',))
                else:
                    cur.execute("""
                        SELECT id, date, content, articles, podcast_script, audio_url
                        FROM news_newsletters 
                        ORDER BY date DESC
                        LIMIT 10
                    """)
                return [dict(row) for row in cur.fetchall()]

    def get_unprocessed_articles(self, since_date):
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM news_articles 
                    WHERE processed_date > %s 
                    ORDER BY processed_date DESC
                """, (since_date,))
                return [dict(row) for row in cur.fetchall()]

    def update_newsletter_audio(self, newsletter_id, audio_url):
        """Update the newsletter with generated audio URL"""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                # First add the audio_url column if it doesn't exist
                cur.execute("""
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name='news_newsletters' 
                            AND column_name='audio_url'
                        ) THEN
                            ALTER TABLE news_newsletters ADD COLUMN audio_url TEXT;
                        END IF;
                    END $$;
                """)

                # Update the newsletter with the audio URL
                cur.execute("""
                    UPDATE news_newsletters 
                    SET audio_url = %s 
                    WHERE id = %s
                """, (audio_url, newsletter_id))