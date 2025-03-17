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
            print(f"\nProcessing source: {url}")
            # Process main page and its article links
            articles = processor.process_article(url, interest_prompt, summary_prompt)

            for article in articles:
                # Only check duplicates for article URLs, not source URLs
                with storage.conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM news_articles WHERE url = %s", (article["url"],))
                    if cur.fetchone():
                        print(f"Skipping duplicate article: {article['url']}")
                        continue

                # Save new article
                storage.save_article(article)
                print(f"Saved new article: {article['title']}")

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

# Store the current scheduler thread to be able to stop it
current_scheduler_thread = None

def run_scheduler(check_interval, newsletter_time):
    """Run the scheduler continuously"""
    # Clear any existing jobs
    schedule.clear()

    # Process URLs at specified interval
    schedule.every(check_interval).hours.do(process_urls)

    # Generate newsletter at specified time
    schedule.every().day.at(newsletter_time).do(generate_daily_newsletter)

    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler(check_interval=1, newsletter_time="08:00"):
    """Start or restart the scheduler with new settings"""
    global current_scheduler_thread

    # Stop existing scheduler if running
    if current_scheduler_thread and current_scheduler_thread.is_alive():
        schedule.clear()
        current_scheduler_thread = None

    # Start new scheduler thread
    current_scheduler_thread = threading.Thread(
        target=run_scheduler,
        args=(check_interval, newsletter_time),
        daemon=True
    )
    current_scheduler_thread.start()
    print(f"Started scheduler: checking URLs every {check_interval} hours, newsletter at {newsletter_time}")