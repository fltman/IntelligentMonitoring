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
    
    urls = storage.get_urls()
    interest_prompt = storage.get_setting("interest_prompt")
    summary_prompt = storage.get_setting("summary_prompt")
    
    for url in urls:
        try:
            article = processor.process_article(url, interest_prompt, summary_prompt)
            if article:
                storage.save_article(article)
        except Exception:
            continue

def generate_daily_newsletter():
    """Generate the daily newsletter"""
    storage = Storage()
    newsletter_gen = NewsletterGenerator()
    
    # Get articles from the last 24 hours
    since_date = (datetime.now() - timedelta(days=1)).isoformat()
    articles = storage.get_unprocessed_articles(since_date)
    
    if articles:
        template = storage.get_setting("newsletter_template")
        try:
            newsletter = newsletter_gen.generate_newsletter(articles, template)
            storage.save_newsletter(newsletter)
        except Exception:
            pass

def run_scheduler():
    """Run the scheduler continuously"""
    schedule.every(1).hours.do(process_urls)
    schedule.every().day.at("08:00").do(generate_daily_newsletter)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler():
    """Start the scheduler in a background thread"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
