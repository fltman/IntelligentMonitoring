from datetime import datetime
from openai import OpenAI
import os
import json

class PodcastGenerator:

    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_podcast_script(self, articles, prompt):
        """Generate a podcast script from the articles using the prompt"""
        try:
            # Prepare articles data
            articles_data = []
            for article in articles:
                articles_data.append({
                    "title": article["title"],
                    "summary": article["summary"],
                    "url": article["url"]
                })

            # Use OpenAI to generate the podcast script
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": "You are a podcast script generator. "
                    "Create a podcast script using the provided articles and prompt. "
                    "The script should be engaging and follow the specified format."
                }, {
                    "role": "user",
                    "content": f"Prompt:\n{prompt}\n\n"
                    f"Articles:\n{json.dumps(articles_data, indent=2)}"
                }],
                response_format={"type": "json_object"}
            )

            # Parse the response
            podcast_data = json.loads(response.choices[0].message.content)
            return podcast_data

        except Exception as e:
            raise Exception(f"Failed to generate podcast script: {str(e)}")
