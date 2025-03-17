import schedule
import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.article_processor import ArticleProcessor
from utils.storage import Storage
from utils.newsletter import NewsletterGenerator

def process_urls(status_callback=None):
    """Process all URLs and generate newsletter"""
    storage = Storage()
    processor = ArticleProcessor()

    # Get configuration
    urls = storage.get_urls()
    interest_prompt = storage.get_setting("interest_prompt")
    summary_prompt = storage.get_setting("summary_prompt")

    if not interest_prompt or not summary_prompt:
        error_msg = "Missing prompts configuration"
        if status_callback:
            status_callback(error_msg)
        print(error_msg)
        return

    def process_single_url(url):
        """Process a single URL and its articles"""
        try:
            if status_callback:
                status_callback(f"Processing source: {url}")
            print(f"\nProcessing source: {url}")
            return processor.process_article(url, interest_prompt, summary_prompt, status_callback)
        except Exception as e:
            error_msg = f"Error processing URL {url}: {str(e)}"
            if status_callback:
                status_callback(error_msg)
            print(error_msg)
            return []

    # Process URLs in parallel with max 5 workers
    processed_articles = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(process_single_url, url): url for url in urls}

        for future in as_completed(future_to_url):
            articles = future.result()
            if articles:
                for article in articles:
                    # Check for duplicates
                    with storage.get_conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT 1 FROM news_articles WHERE url = %s", (article["url"],))
                            if cur.fetchone():
                                msg = f"Skipping duplicate article: {article['url']}"
                                if status_callback:
                                    status_callback(msg)
                                print(msg)
                                continue

                    # Save new article
                    storage.save_article(article)
                    msg = f"Saved new article: {article['title']}"
                    if status_callback:
                        status_callback(msg)
                    print(msg)

    # Generate newsletter after processing all URLs
    if status_callback:
        status_callback("Generating newsletter...")
    generate_daily_newsletter()
    if status_callback:
        status_callback("Newsletter generated!")

def generate_daily_newsletter():
    """Generate the daily newsletter"""
    storage = Storage()
    newsletter_gen = NewsletterGenerator()

    # Get template and podcast settings
    template = storage.get_setting("newsletter_template")
    create_podcast = storage.get_setting("create_podcast", "false") == "true"
    podcast_prompt = storage.get_setting("podcast_studio_prompt", "")

    if not template:
        print("Missing newsletter template")
        return

    # Get articles from the last 24 hours
    since_date = (datetime.now() - timedelta(days=1)).isoformat()
    articles = storage.get_unprocessed_articles(since_date)

    if articles:
        try:
            newsletter = newsletter_gen.generate_newsletter(
                articles, 
                template,
                create_podcast=create_podcast,
                podcast_prompt=podcast_prompt
            )
            storage.save_newsletter(newsletter)
            print(f"Generated newsletter with {len(articles)} articles")
        except Exception as e:
            print(f"Error generating newsletter: {str(e)}")

# Store the current scheduler thread to be able to stop it
current_scheduler_thread = None

def run_scheduler(newsletter_time):
    """Run the scheduler continuously"""
    # Clear any existing jobs
    schedule.clear()

    # Generate newsletter at specified time
    schedule.every().day.at(newsletter_time).do(process_urls)

    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler(newsletter_time="08:00"):
    """Start or restart the scheduler with new settings"""
    global current_scheduler_thread

    # Stop existing scheduler if running
    if current_scheduler_thread and current_scheduler_thread.is_alive():
        schedule.clear()
        current_scheduler_thread = None

    # Start new scheduler thread
    current_scheduler_thread = threading.Thread(
        target=run_scheduler,
        args=(newsletter_time,),
        daemon=True
    )
    current_scheduler_thread.start()
    print(f"Started scheduler: generating newsletter at {newsletter_time}")