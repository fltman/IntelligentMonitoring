import json
import os
from datetime import datetime
import urllib.parse

class Storage:
    def __init__(self):
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/articles", exist_ok=True)
        os.makedirs("data/newsletters", exist_ok=True)
        
        self.settings_file = "data/settings.json"
        self.urls_file = "data/urls.json"
        
        # Initialize storage files if they don't exist
        if not os.path.exists(self.settings_file):
            self._save_json(self.settings_file, {})
        if not os.path.exists(self.urls_file):
            self._save_json(self.urls_file, [])

    def _load_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def _save_json(self, file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_setting(self, key, default=""):
        settings = self._load_json(self.settings_file)
        return settings.get(key, default)

    def save_setting(self, key, value):
        settings = self._load_json(self.settings_file)
        settings[key] = value
        self._save_json(self.settings_file, settings)

    def add_url(self, url):
        try:
            # Basic URL validation
            result = urllib.parse.urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False
                
            urls = self._load_json(self.urls_file)
            if url not in urls:
                urls.append(url)
                self._save_json(self.urls_file, urls)
                return True
            return False
        except:
            return False

    def remove_url(self, url):
        urls = self._load_json(self.urls_file)
        if url in urls:
            urls.remove(url)
            self._save_json(self.urls_file, urls)

    def get_urls(self):
        return self._load_json(self.urls_file)

    def save_article(self, article):
        filename = f"data/articles/{article['processed_date']}.json"
        self._save_json(filename, article)

    def get_recent_articles(self, limit=10):
        articles = []
        try:
            files = sorted(os.listdir("data/articles"), reverse=True)
            for file in files[:limit]:
                article = self._load_json(os.path.join("data/articles", file))
                if article:
                    articles.append(article)
        except Exception:
            pass
        return articles

    def save_newsletter(self, newsletter):
        filename = f"data/newsletters/{newsletter['date']}.json"
        self._save_json(filename, newsletter)

    def get_newsletters(self, search_term=None):
        newsletters = []
        try:
            files = sorted(os.listdir("data/newsletters"), reverse=True)
            for file in files:
                newsletter = self._load_json(os.path.join("data/newsletters", file))
                if newsletter:
                    if not search_term or search_term.lower() in newsletter['content'].lower():
                        newsletters.append(newsletter)
        except Exception:
            pass
        return newsletters

    def get_unprocessed_articles(self, since_date):
        articles = []
        try:
            files = os.listdir("data/articles")
            for file in files:
                article = self._load_json(os.path.join("data/articles", file))
                if article and article['processed_date'] > since_date:
                    articles.append(article)
        except Exception:
            pass
        return articles
