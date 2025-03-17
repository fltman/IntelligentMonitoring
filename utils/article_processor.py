import trafilatura
from openai import OpenAI
import os
from datetime import datetime
import json

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
            return content
        except Exception as e:
            raise Exception(f"Failed to fetch article: {str(e)}")

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
        content = self.fetch_article(url)
        relevant, reason = self.check_relevance(content, interest_prompt)
        
        if not relevant:
            return None
            
        title, summary = self.summarize_article(content, summary_prompt)
        
        return {
            "url": url,
            "title": title,
            "summary": summary,
            "processed_date": datetime.now().isoformat(),
            "content": content
        }
