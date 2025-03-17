import trafilatura
from openai import OpenAI
import os
from datetime import datetime
import json
from urllib.parse import urljoin, urlparse
import re

class ArticleProcessor:
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def fetch_article(self, url):
        """Fetch and extract content from a URL"""
        try:
            downloaded = trafilatura.fetch_url(url)
            content = trafilatura.extract(downloaded)
            if not content:
                raise Exception("No content could be extracted")
            return content, self._extract_article_links(downloaded, url)
        except Exception as e:
            raise Exception(f"Failed to fetch article: {str(e)}")

    def _extract_article_links(self, html_content, base_url):
        """Extract potential article links from HTML content"""
        links = []
        try:
            # Use trafilatura to extract links
            links_data = trafilatura.extract_metadata(html_content)
            if links_data and 'links' in links_data:
                links.extend(links_data['links'])

            # Clean and normalize links
            cleaned_links = []
            for link in links:
                # Make relative URLs absolute
                absolute_url = urljoin(base_url, link)

                # Basic filtering for likely article URLs
                parsed = urlparse(absolute_url)
                if any(pattern in parsed.path.lower() for pattern in ['/article/', '/news/', '/story/']):
                    cleaned_links.append(absolute_url)

            return list(set(cleaned_links))  # Remove duplicates
        except Exception as e:
            print(f"Warning: Error extracting links: {str(e)}")
            return []

    def check_relevance(self, content, interest_prompt):
        """Check if the article is relevant based on interest prompt"""
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an article relevance checker. "
                     "Determine if the article matches the given interests. "
                     "Respond with JSON in this format: "
                     "{'relevant': boolean, 'reason': string}"},
                    {"role": "user", "content": f"Interest criteria:\n{interest_prompt}\n\n"
                     f"Article content:\n{content[:4000]}"}  # Limit content length
                ],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return result["relevant"], result["reason"]
        except Exception as e:
            raise Exception(f"Failed to check relevance: {str(e)}")

    def summarize_article(self, content, summary_prompt):
        """Summarize the article based on summary prompt"""
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an article summarizer. "
                     "Summarize the article according to the given instructions. "
                     "Respond with JSON in this format: "
                     "{'title': string, 'summary': string}"},
                    {"role": "user", "content": f"Summary instructions:\n{summary_prompt}\n\n"
                     f"Article content:\n{content[:4000]}"}
                ],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return result["title"], result["summary"]
        except Exception as e:
            raise Exception(f"Failed to summarize article: {str(e)}")

    def process_article(self, url, interest_prompt, summary_prompt):
        """Process an article through the complete pipeline"""
        content, article_links = self.fetch_article(url)

        # First check if the main page content is relevant
        relevant, reason = self.check_relevance(content, interest_prompt)
        processed_articles = []

        if relevant:
            title, summary = self.summarize_article(content, summary_prompt)
            processed_articles.append({
                "url": url,
                "title": title,
                "summary": summary,
                "processed_date": datetime.now().isoformat(),
                "content": content
            })
            print(f"Found relevant content on main page: {title}")

        # Process extracted article links
        for article_url in article_links:
            try:
                print(f"Checking article: {article_url}")
                article_content, _ = self.fetch_article(article_url)  # Ignore nested links
                relevant, reason = self.check_relevance(article_content, interest_prompt)

                if relevant:
                    title, summary = self.summarize_article(article_content, summary_prompt)
                    processed_articles.append({
                        "url": article_url,
                        "title": title,
                        "summary": summary,
                        "processed_date": datetime.now().isoformat(),
                        "content": article_content
                    })
                    print(f"Found relevant article: {title}")
            except Exception as e:
                print(f"Error processing article {article_url}: {str(e)}")
                continue

        return processed_articles