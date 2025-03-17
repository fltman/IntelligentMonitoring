import streamlit as st
import json
from datetime import datetime
from utils.article_processor import ArticleProcessor
from utils.storage import Storage
from utils.newsletter import NewsletterGenerator
from utils.scheduler import start_scheduler

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
        
        # Save settings
        if st.button("Save Configuration"):
            storage.save_setting("interest_prompt", interest_prompt)
            storage.save_setting("summary_prompt", summary_prompt)
            storage.save_setting("newsletter_template", newsletter_template)
            st.success("Configuration saved!")

    # Main content area
    tab1, tab2, tab3 = st.tabs(["URL Management", "Recent Articles", "Newsletter Archive"])

    # URL Management tab
    with tab1:
        st.header("URL Management")
        
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
    # Start the scheduler in the background
    start_scheduler()
    main()
