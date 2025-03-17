from datetime import datetime
from openai import OpenAI
import os
import json
from utils.podcast import PodcastGenerator

class NewsletterGenerator:

    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.podcast_gen = PodcastGenerator()

    def generate_newsletter(self, articles, template, create_podcast=False, podcast_prompt=""):
        """Generate a newsletter from the collected articles using the template"""
        try:
            # Prepare articles data
            articles_data = []
            for article in articles:
                articles_data.append({
                    "title": article["title"],
                    "summary": article["summary"],
                    "url": article["url"]
                })

            # Use OpenAI to generate the newsletter
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role":
                    "system",
                    "content":
                    "You are a newsletter generator. "
                    "Create a newsletter using the provided template and articles. "
                    "The newsletter should be well-structured and engaging."
                }, {
                    "role":
                    "user",
                    "content":
                    f"Template:\n{template}\n\n"
                    f"Articles:\n{json.dumps(articles_data, indent=2)}"
                }])

            newsletter_content = response.choices[0].message.content

            result = {
                "date": datetime.now().isoformat(),
                "content": newsletter_content,
                "articles": articles_data
            }

            # Generate podcast script if enabled
            if create_podcast and podcast_prompt:
                result["podcast_script"] = self.podcast_gen.generate_podcast_script(
                    articles, podcast_prompt
                )

            return result
        except Exception as e:
            raise Exception(f"Failed to generate newsletter: {str(e)}")