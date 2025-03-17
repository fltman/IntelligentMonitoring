import schedule
import time
import threading
from datetime import datetime, timedelta
from utils.article_processor import ArticleProcessor
from utils.storage import Storage
from utils.newsletter import NewsletterGenerator

def process_urls():
    """Process all URLs and check for new articles"""
    storage = Storage()
    processor = ArticleProcessor()

    # Get configuration
    urls = storage.get_urls()
    interest_prompt = storage.get_setting("interest_prompt")
    summary_prompt = storage.get_setting("summary_prompt")

    if not interest_prompt or not summary_prompt:
        print("Missing prompts configuration")
        return

    for url in urls:
        try:
            # Check if article already exists
            with storage.conn.cursor() as cur:
                cur.execute("SELECT 1 FROM news_articles WHERE url = %s", (url,))
                if cur.fetchone():
                    continue

            # Process new article
            article = processor.process_article(url, interest_prompt, summary_prompt)
            if article:
                storage.save_article(article)
                print(f"Processed new article: {article['title']}")
        except Exception as e:
            print(f"Error processing URL {url}: {str(e)}")
            continue

def generate_daily_newsletter():
    """Generate the daily newsletter"""
    storage = Storage()
    newsletter_gen = NewsletterGenerator()

    # Get template
    template = storage.get_setting("newsletter_template")
    if not template:
        print("Missing newsletter template")
        return

    # Get articles from the last 24 hours
    since_date = (datetime.now() - timedelta(days=1)).isoformat()
    articles = storage.get_unprocessed_articles(since_date)

    if articles:
        try:
            newsletter = newsletter_gen.generate_newsletter(articles, template)
            storage.save_newsletter(newsletter)
            print(f"Generated newsletter with {len(articles)} articles")
        except Exception as e:
            print(f"Error generating newsletter: {str(e)}")

def run_scheduler():
    """Run the scheduler continuously"""
    # Process URLs every hour
    schedule.every(1).hours.do(process_urls)

    # Generate newsletter at 8 AM daily
    schedule.every().day.at("08:00").do(generate_daily_newsletter)

    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler():
    """Start the scheduler in a background thread"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("Started background scheduler")