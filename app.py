import streamlit as st
import json
from datetime import datetime
from utils.article_processor import ArticleProcessor
from utils.storage import Storage
from utils.newsletter import NewsletterGenerator
from utils.scheduler import start_scheduler, process_urls, generate_daily_newsletter

# Initialize storage and processors
storage = Storage()
article_processor = ArticleProcessor()
newsletter_generator = NewsletterGenerator()

def main():
    st.title("AI-Driven News Monitoring System")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        # Interest prompt
        interest_prompt = st.text_area(
            "Interest Prompt",
            value=storage.get_setting("interest_prompt", ""),
            help="Describe what kind of articles interest you"
        )

        # Summary prompt
        summary_prompt = st.text_area(
            "Summary Prompt",
            value=storage.get_setting("summary_prompt", ""),
            help="Define how articles should be summarized"
        )

        # Newsletter template
        newsletter_template = st.text_area(
            "Newsletter Template",
            value=storage.get_setting("newsletter_template", ""),
            help="Define the structure of your newsletter"
        )

        # Scheduler settings
        st.subheader("Scheduler Settings")
        url_check_interval = st.number_input(
            "URL Check Interval (hours)",
            min_value=1,
            max_value=24,
            value=int(storage.get_setting("url_check_interval", "1")),
            help="How often to check URLs for new content"
        )

        newsletter_time = st.time_input(
            "Newsletter Generation Time",
            datetime.strptime(storage.get_setting("newsletter_time", "08:00"), "%H:%M").time(),
            help="When to generate the daily newsletter"
        )

        # Save settings
        if st.button("Save Configuration"):
            storage.save_setting("interest_prompt", interest_prompt)
            storage.save_setting("summary_prompt", summary_prompt)
            storage.save_setting("newsletter_template", newsletter_template)
            storage.save_setting("url_check_interval", str(url_check_interval))
            storage.save_setting("newsletter_time", newsletter_time.strftime("%H:%M"))
            st.success("Configuration saved!")
            # Restart scheduler with new settings
            start_scheduler(url_check_interval, newsletter_time.strftime("%H:%M"))

    # Main content area
    tab1, tab2, tab3 = st.tabs(["URL Management", "Recent Articles", "Newsletter Archive"])

    # URL Management tab
    with tab1:
        st.header("URL Management")

        # Status container for processing feedback
        status_container = st.empty()

        # Check URLs button
        if st.button("Process URLs and Generate Newsletter"):
            with st.spinner("Processing URLs and generating newsletter..."):
                # Create a status container
                status = st.status("Processing URLs...")

                def status_callback(message):
                    status.update(label=message)

                try:
                    process_urls(status_callback)
                    status.update(label="Newsletter generated and updates completed!", state="complete")
                except Exception as e:
                    status.update(label=f"Error: {str(e)}", state="error")

        st.divider()

        # Add new URL
        new_url = st.text_input("Add New URL")
        if st.button("Add URL"):
            if new_url:
                if storage.add_url(new_url):
                    st.success("URL added successfully!")
                else:
                    st.error("URL already exists or is invalid")

        # Display existing URLs
        urls = storage.get_urls()
        if urls:
            st.subheader("Monitored URLs")
            for url in urls:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(url)
                with col2:
                    if st.button("Remove", key=f"remove_{url}"):
                        storage.remove_url(url)
                        st.rerun()

    # Recent Articles tab
    with tab2:
        st.header("Recent Articles")
        articles = storage.get_recent_articles()

        if not articles:
            st.info("No recent articles found")
        else:
            for article in articles:
                with st.expander(article['title']):
                    st.write(f"Source: {article['url']}")
                    st.write(f"Processed: {article['processed_date']}")
                    st.write("Summary:")
                    st.write(article['summary'])

    # Newsletter Archive tab
    with tab3:
        st.header("Newsletter Archive")

        # Search functionality
        search_term = st.text_input("Search newsletters")

        newsletters = storage.get_newsletters(search_term)
        if not newsletters:
            st.info("No newsletters found")
        else:
            for newsletter in newsletters:
                with st.expander(f"Newsletter - {newsletter['date']}"):
                    st.write(newsletter['content'])

if __name__ == "__main__":
    # Get initial scheduler settings
    url_check_interval = int(storage.get_setting("url_check_interval", "1"))
    newsletter_time = storage.get_setting("newsletter_time", "08:00")

    # Start the scheduler in the background
    start_scheduler(url_check_interval, newsletter_time)
    main()