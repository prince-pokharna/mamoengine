"""
Configuration management for Market-Mood Engine.
Loads environment variables and provides configuration settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Database
DB_PATH = os.getenv("DB_PATH", "data/market_mood.db")

# Data Collection Settings
KEYWORDS = [
    "tech", "phones", "fashion", "food", "ecommerce", "startups",
    "Flipkart", "Amazon India", "OnePlus", "new phone", "gadgets"
]

CATEGORIES = ["phones", "laptops", "fashion", "home", "food"]

SUBREDDITS = ["india", "IndianGaming", "BudgetPhones"]

# Rate Limiting
TWITTER_RATE_LIMIT_TWEETS = 450  # per 15 minutes
TWITTER_RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds

# Data Quality
MIN_ARTICLE_CONTENT_LENGTH = 50
MIN_TWEET_LENGTH = 10
MAX_TWEET_LENGTH = 280
MIN_RETWEETS = 2
MIN_LIKES = 1

# Retry Settings
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 1s, 2s, 4s
