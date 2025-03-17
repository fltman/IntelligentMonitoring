import trafilatura
from openai import OpenAI
import os
from datetime import datetime
import json
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup


class ArticleProcessor:

    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def fetch_article(self, url):
        """Fetch and extract content from a URL"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                raise Exception("Could not download the content")

            # Extract article links before extracting main content
            article_links = self._extract_article_links(downloaded, url)

            # Extract main content
            content = trafilatura.extract(downloaded)
            if not content:
                raise Exception("No content could be extracted")

            return content, article_links
        except Exception as e:
            raise Exception(f"Failed to fetch article: {str(e)}")

    def _extract_article_links(self, html_content, base_url):
        """Extract potential article links from HTML content"""
        links = set()  # Use set to avoid duplicates
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Get links from common article containers
            article_containers = soup.find_all(
                ['article', 'div', 'section'],
                class_=lambda x: x and any(term in x.lower(
                ) for term in ['article', 'post', 'story', 'news']))

            # Extract links from article containers
            for container in article_containers:
                for a_tag in container.find_all('a', href=True):
                    links.add(a_tag['href'])

            # Also check for links in the main content area
            main_content = soup.find(
                ['main', 'div'], class_=lambda x: x and 'content' in x.lower())
            if main_content:
                for a_tag in main_content.find_all('a', href=True):
                    links.add(a_tag['href'])

            # Clean and normalize links
            cleaned_links = []
            for link in links:
                # Make relative URLs absolute
                absolute_url = urljoin(base_url, link)
                parsed = urlparse(absolute_url)

                # Skip if not same domain or obvious non-article URLs
                if not parsed.netloc or any(
                        skip in parsed.path.lower() for skip in
                    ['/tag/', '/category/', '/author/', '/search/', '/page/']):
                    continue

                # Include if likely an article URL
                if any(pattern in parsed.path.lower() for pattern in [
                        '/article/', '/news/', '/story/', '/post/', '/2024/',
                        '/2025/'
                ]):
                    cleaned_links.append(absolute_url)

            return list(set(cleaned_links))  # Remove any remaining duplicates
        except Exception as e:
            print(f"Warning: Error extracting links: {str(e)}")
            return []

    def check_relevance(self, content, interest_prompt):
        """Check if the article is relevant based on interest prompt"""
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role":
                        "system",
                        "content":
                        "You are an article relevance checker. "
                        "Determine if the article matches the given interests. "
                        "Respond with JSON in this format: "
                        "{'relevant': boolean, 'reason': string}"
                    },
                    {
                        "role":
                        "user",
                        "content":
                        f"Interest criteria:\n{interest_prompt}\n\n"
                        f"Article content:\n{content[:4000]}"
                    }  # Limit content length
                ],
                response_format={"type": "json_object"})
            result = json.loads(response.choices[0].message.content)
            return result["relevant"], result["reason"]
        except Exception as e:
            raise Exception(f"Failed to check relevance: {str(e)}")

    def summarize_article(self, content, summary_prompt):
        """Summarize the article based on summary prompt"""
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role":
                    "system",
                    "content":
                    "You are an article summarizer. "
                    "Summarize the article according to the given instructions. "
                    "Respond with JSON in this format: "
                    "{'title': string, 'summary': string}"
                }, {
                    "role":
                    "user",
                    "content":
                    f"Summary instructions:\n{summary_prompt}\n\n"
                    f"Article content:\n{content[:4000]}"
                }],
                response_format={"type": "json_object"})
            result = json.loads(response.choices[0].message.content)
            return result["title"], result["summary"]
        except Exception as e:
            raise Exception(f"Failed to summarize article: {str(e)}")

    def process_article(self, url, interest_prompt, summary_prompt,
                       status_callback=None):
        """Process an article through the complete pipeline"""
        if status_callback:
            status_callback(f"Hämtar innehåll från: {url}")
        print(f"Processing URL: {url}")
        content, article_links = self.fetch_article(url)
        processed_articles = []

        # First check if the main page content is relevant
        relevant, reason = self.check_relevance(content, interest_prompt)

        if relevant:
            title, summary = self.summarize_article(content, summary_prompt)
            processed_articles.append({
                "url":
                url,
                "title":
                title,
                "summary":
                summary,
                "processed_date":
                datetime.now().isoformat(),
                "content":
                content
            })
            msg = f"Hittade relevant innehåll på huvudsidan: {title}"
            if status_callback:
                status_callback(msg)
            print(f"Found relevant content on main page: {title}")

        # Process extracted article links
        if article_links:
            msg = f"Hittade {len(article_links)} potentiella artikellänkar"
            if status_callback:
                status_callback(msg)
            print(f"Found {len(article_links)} potential article links")

            for article_url in article_links:
                try:
                    if status_callback:
                        status_callback(f"Kontrollerar artikel: {article_url}")
                    print(f"Checking article: {article_url}")
                    article_content, _ = self.fetch_article(
                        article_url)  # Ignore nested links
                    relevant, reason = self.check_relevance(
                        article_content, interest_prompt)

                    if relevant:
                        title, summary = self.summarize_article(
                            article_content, summary_prompt)
                        processed_articles.append({
                            "url":
                            article_url,
                            "title":
                            title,
                            "summary":
                            summary,
                            "processed_date":
                            datetime.now().isoformat(),
                            "content":
                            article_content
                        })
                        msg = f"Hittade relevant artikel: {title}"
                        if status_callback:
                            status_callback(msg)
                        print(f"Found relevant article: {title}")
                except Exception as e:
                    msg = f"Fel vid bearbetning av artikel {article_url}: {str(e)}"
                    if status_callback:
                        status_callback(msg)
                    print(f"Error processing article {article_url}: {str(e)}")
                    continue

        return processed_articles