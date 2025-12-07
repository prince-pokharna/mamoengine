"""
Data ingestion pipeline for Market-Mood Engine.
Collects data from multiple sources: News API, Twitter, Google Trends, and mock e-commerce/Reddit data.
"""
import logging
import time
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

try:
    from newsapi import NewsApiClient
except ImportError:
    NewsApiClient = None

try:
    import tweepy
except ImportError:
    tweepy = None

try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None

import config
from src.models import Article, Tweet, GoogleTrend, EcommerceSale, RedditPost
from src.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for data collectors."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    def collect(self) -> List[Any]:
        """Collect data from source."""
        pass
    
    def retry_with_backoff(self, func, max_retries: int = 3) -> Any:
        """Execute function with exponential backoff retry logic."""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"{self.name} failed after {max_retries} attempts: {e}")
                    raise
                wait_time = config.RETRY_BACKOFF_FACTOR ** attempt
                logger.warning(f"{self.name} attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)


class NewsCollector(BaseCollector):
    """Collects news articles from NewsAPI."""
    
    def __init__(self):
        super().__init__()
        if NewsApiClient and config.NEWS_API_KEY:
            try:
                self.client = NewsApiClient(api_key=config.NEWS_API_KEY)
            except Exception as e:
                logger.warning(f"NewsAPI client initialization failed: {e}")
                self.client = None
        else:
            logger.warning("NewsAPI not available or API key not set")
            self.client = None
        
        self.keywords = ["tech", "phones", "fashion", "food", "ecommerce", "startups"]
        self.exclude_keywords = ["sports", "politics", "entertainment"]
    
    def collect(self) -> List[Article]:
        """Collect news articles from NewsAPI."""
        if not self.client:
            logger.info("NewsAPI client not available, returning mock data")
            return self._generate_mock_articles()
        
        def _fetch():
            articles = []
            for keyword in self.keywords:
                try:
                    response = self.client.get_everything(
                        q=keyword,
                        language='en',
                        sort_by='publishedAt',
                        page_size=10,
                        from_param=(datetime.now() - timedelta(hours=24)).isoformat()
                    )
                    
                    if response['status'] == 'ok':
                        for article_data in response.get('articles', []):
                            # Filter out unwanted content
                            title = article_data.get('title', '')
                            content = article_data.get('description', '') or article_data.get('content', '')
                            
                            if len(content) < config.MIN_ARTICLE_CONTENT_LENGTH:
                                continue
                            
                            # Check for exclude keywords
                            if any(exc in title.lower() or exc in content.lower() 
                                   for exc in self.exclude_keywords):
                                continue
                            
                            article = Article(
                                source=article_data.get('source', {}).get('name', 'unknown'),
                                title=title,
                                content=content,
                                published_date=datetime.fromisoformat(
                                    article_data['publishedAt'].replace('Z', '+00:00')
                                ),
                                url=article_data.get('url', ''),
                                fetched_date=datetime.now()
                            )
                            articles.append(article)
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error fetching news for keyword '{keyword}': {e}")
            
            return articles
        
        try:
            articles = self.retry_with_backoff(_fetch)
            logger.info(f"Collected {len(articles)} articles from NewsAPI")
            return articles
        except Exception as e:
            logger.error(f"NewsCollector failed: {e}")
            return self._generate_mock_articles()
    
    def _generate_mock_articles(self) -> List[Article]:
        """Generate mock articles for testing."""
        mock_data = [
            {
                "source": "TechCrunch",
                "title": "OnePlus 13 launches with groundbreaking camera technology",
                "content": "OnePlus has unveiled its latest flagship smartphone, the OnePlus 13, featuring a revolutionary camera system that promises to change mobile photography. The device includes advanced AI processing and improved low-light performance."
            },
            {
                "source": "Economic Times",
                "title": "Flipkart sees record sales during festive season",
                "content": "E-commerce giant Flipkart reported unprecedented sales figures during the festive shopping season, with electronics and fashion categories leading the growth. The company attributes success to competitive pricing and faster delivery."
            },
            {
                "source": "Fashion Forward",
                "title": "Sustainable fashion trend gaining momentum in India",
                "content": "Indian consumers are increasingly choosing sustainable and eco-friendly fashion brands. Market research shows a 45% increase in demand for sustainable clothing over the past year, signaling a major shift in consumer preferences."
            },
            {
                "source": "Food Business News",
                "title": "Cloud kitchen startups attract major investments",
                "content": "The cloud kitchen segment in India has attracted over $500 million in investments this year. Investors are betting on the growing demand for food delivery services and the low overhead costs of cloud-based operations."
            },
            {
                "source": "Startup India",
                "title": "EdTech startups pivot to hybrid learning models",
                "content": "Educational technology companies are adapting to post-pandemic realities by offering hybrid learning solutions. The shift combines online convenience with offline engagement, addressing concerns about screen time and social interaction."
            }
        ]
        
        articles = []
        for item in mock_data:
            article = Article(
                source=item["source"],
                title=item["title"],
                content=item["content"],
                published_date=datetime.now() - timedelta(hours=random.randint(1, 12)),
                url=f"https://example.com/article-{random.randint(1000, 9999)}",
                fetched_date=datetime.now()
            )
            articles.append(article)
        
        logger.info(f"Generated {len(articles)} mock articles")
        return articles


class TwitterCollector(BaseCollector):
    """Collects tweets from Twitter API."""
    
    def __init__(self):
        super().__init__()
        if tweepy and all([config.TWITTER_API_KEY, config.TWITTER_API_SECRET]):
            try:
                self.client = tweepy.Client(
                    bearer_token=None,
                    consumer_key=config.TWITTER_API_KEY,
                    consumer_secret=config.TWITTER_API_SECRET,
                    access_token=config.TWITTER_ACCESS_TOKEN,
                    access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET
                )
            except Exception as e:
                logger.warning(f"Twitter client initialization failed: {e}")
                self.client = None
        else:
            logger.warning("Twitter API not available or credentials not set")
            self.client = None
        
        self.keywords = ["Flipkart", "Amazon India", "OnePlus", "new phone", "gadgets"]
    
    def collect(self) -> List[Tweet]:
        """Collect tweets from Twitter API."""
        if not self.client:
            logger.info("Twitter client not available, returning mock data")
            return self._generate_mock_tweets()
        
        def _fetch():
            tweets = []
            for keyword in self.keywords:
                try:
                    response = self.client.search_recent_tweets(
                        query=keyword,
                        max_results=30,
                        tweet_fields=['created_at', 'public_metrics', 'author_id']
                    )
                    
                    if response.data:
                        for tweet_data in response.data:
                            metrics = tweet_data.public_metrics
                            
                            # Filter based on engagement
                            if (metrics['retweet_count'] < config.MIN_RETWEETS or 
                                metrics['like_count'] < config.MIN_LIKES):
                                continue
                            
                            tweet = Tweet(
                                text=tweet_data.text,
                                author=str(tweet_data.author_id),
                                created_date=tweet_data.created_at,
                                likes=metrics['like_count'],
                                retweets=metrics['retweet_count'],
                                source_name='twitter',
                                fetched_date=datetime.now()
                            )
                            tweets.append(tweet)
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error fetching tweets for '{keyword}': {e}")
            
            return tweets
        
        try:
            tweets = self.retry_with_backoff(_fetch)
            logger.info(f"Collected {len(tweets)} tweets from Twitter")
            return tweets
        except Exception as e:
            logger.error(f"TwitterCollector failed: {e}")
            return self._generate_mock_tweets()
    
    def _generate_mock_tweets(self) -> List[Tweet]:
        """Generate mock tweets for testing."""
        mock_data = [
            "Just ordered the new OnePlus 13! The camera specs look incredible 📸",
            "Flipkart's Big Billion Days sale is insane! Got a laptop at 40% off 💻",
            "Amazon India delivery never disappoints. Ordered yesterday, arrived today! ⚡",
            "The new phone launches are getting boring. Where's the innovation? 🤔",
            "Finally upgraded to 5G. The speed difference is unbelievable! 🚀",
            "Anyone else obsessed with the new gadgets coming out this month? 🎮",
            "Best purchase of the year from Amazon - this smart home device is life-changing",
            "Flipkart customer service is top-notch. They resolved my issue in minutes 👍",
            "The tech market in India is booming! So many exciting options now",
            "New phones are great but why so expensive? Budget options needed 💸"
        ]
        
        tweets = []
        for text in mock_data:
            tweet = Tweet(
                text=text,
                author=f"user_{random.randint(1000, 9999)}",
                created_date=datetime.now() - timedelta(minutes=random.randint(10, 300)),
                likes=random.randint(5, 100),
                retweets=random.randint(2, 50),
                source_name='twitter',
                fetched_date=datetime.now()
            )
            tweets.append(tweet)
        
        logger.info(f"Generated {len(tweets)} mock tweets")
        return tweets


class GoogleTrendsCollector(BaseCollector):
    """Collects search volume data from Google Trends."""
    
    def __init__(self):
        super().__init__()
        if TrendReq:
            try:
                self.client = TrendReq(hl='en-US', tz=330)  # IST timezone
            except Exception as e:
                logger.warning(f"PyTrends initialization failed: {e}")
                self.client = None
        else:
            logger.warning("PyTrends not available")
            self.client = None
        
        self.keywords = ["OnePlus", "iPhone", "Amazon India", "Flipkart", "laptops"]
    
    def collect(self) -> List[GoogleTrend]:
        """Collect Google Trends data."""
        if not self.client:
            logger.info("PyTrends client not available, returning mock data")
            return self._generate_mock_trends()
        
        def _fetch():
            trends = []
            try:
                # Build payload for keywords
                self.client.build_payload(
                    self.keywords,
                    timeframe='now 1-d',
                    geo='IN'
                )
                
                # Get interest over time
                interest_df = self.client.interest_over_time()
                
                if not interest_df.empty:
                    for keyword in self.keywords:
                        if keyword in interest_df.columns:
                            latest_value = int(interest_df[keyword].iloc[-1])
                            
                            trend = GoogleTrend(
                                keyword=keyword,
                                search_volume=latest_value,
                                date=datetime.now(),
                                category='technology',
                                fetched_date=datetime.now()
                            )
                            trends.append(trend)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching Google Trends: {e}")
            
            return trends
        
        try:
            trends = self.retry_with_backoff(_fetch)
            logger.info(f"Collected {len(trends)} Google Trends")
            return trends
        except Exception as e:
            logger.error(f"GoogleTrendsCollector failed: {e}")
            return self._generate_mock_trends()
    
    def _generate_mock_trends(self) -> List[GoogleTrend]:
        """Generate mock trends for testing."""
        trends = []
        for keyword in self.keywords:
            trend = GoogleTrend(
                keyword=keyword,
                search_volume=random.randint(50, 100),
                date=datetime.now(),
                category='technology',
                fetched_date=datetime.now()
            )
            trends.append(trend)
        
        logger.info(f"Generated {len(trends)} mock trends")
        return trends


class MockEcommerceCollector(BaseCollector):
    """Simulates e-commerce sales data."""
    
    def __init__(self):
        super().__init__()
        self.categories = config.CATEGORIES
    
    def collect(self) -> List[EcommerceSale]:
        """Generate realistic e-commerce sales data."""
        sales = []
        current_time = datetime.now()
        
        # Weekend vs weekday factor
        is_weekend = current_time.weekday() >= 5
        weekend_multiplier = 1.5 if is_weekend else 1.0
        
        # Time of day factor
        hour = current_time.hour
        if 9 <= hour <= 12:
            time_multiplier = 1.2  # Morning peak
        elif 18 <= hour <= 22:
            time_multiplier = 1.5  # Evening peak
        else:
            time_multiplier = 0.8  # Off-peak
        
        base_sales = {
            "phones": 5000,
            "laptops": 2000,
            "fashion": 8000,
            "home": 3000,
            "food": 12000
        }
        
        for category in self.categories:
            base = base_sales.get(category, 1000)
            variance = random.uniform(0.8, 1.2)
            sales_count = int(base * weekend_multiplier * time_multiplier * variance)
            
            sale = EcommerceSale(
                category=category,
                sales_count=sales_count,
                date=current_time,
                region="India",
                fetched_date=current_time
            )
            sales.append(sale)
        
        logger.info(f"Generated {len(sales)} e-commerce sales records")
        return sales


class MockRedditCollector(BaseCollector):
    """Simulates Reddit discussion data."""
    
    def __init__(self):
        super().__init__()
        self.subreddits = config.SUBREDDITS
    
    def collect(self) -> List[RedditPost]:
        """Generate realistic Reddit posts."""
        mock_posts = [
            {
                "subreddit": "india",
                "title": "Best budget phones under 20k in 2025?",
                "text": "Looking for recommendations for a reliable phone with good camera and battery life. What are you guys using?"
            },
            {
                "subreddit": "IndianGaming",
                "title": "Finally got my hands on the new gaming laptop!",
                "text": "After months of saving, I got the ASUS ROG. The performance is incredible. Anyone else upgraded recently?"
            },
            {
                "subreddit": "BudgetPhones",
                "title": "OnePlus Nord vs Realme - which one should I pick?",
                "text": "Both are in my budget. Need help deciding which offers better value for money."
            },
            {
                "subreddit": "india",
                "title": "Amazon Prime Day deals worth it this year?",
                "text": "Thinking of getting a new tablet. Are the discounts genuine or just marketing hype?"
            },
            {
                "subreddit": "IndianGaming",
                "title": "Gaming phone or regular flagship?",
                "text": "Is it worth getting a gaming-specific phone or should I just get a regular flagship?"
            }
        ]
        
        posts = []
        for post_data in mock_posts:
            post = RedditPost(
                title=post_data["title"],
                text=post_data["text"],
                subreddit=post_data["subreddit"],
                score=random.randint(10, 500),
                created_date=datetime.now() - timedelta(hours=random.randint(1, 24)),
                fetched_date=datetime.now()
            )
            posts.append(post)
        
        logger.info(f"Generated {len(posts)} Reddit posts")
        return posts


class DataPipeline:
    """Orchestrates data collection from all sources."""
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize data pipeline.
        
        Args:
            db: DatabaseManager instance
        """
        self.db = db
        self.collectors = {
            'news': NewsCollector(),
            'twitter': TwitterCollector(),
            'google_trends': GoogleTrendsCollector(),
            'ecommerce': MockEcommerceCollector(),
            'reddit': MockRedditCollector()
        }
        logger.info("DataPipeline initialized with all collectors")
    
    def run_hourly(self):
        """Execute all collectors and store data."""
        logger.info("=" * 50)
        logger.info("Starting hourly data collection pipeline")
        logger.info("=" * 50)
        
        start_time = time.time()
        stats = {}
        
        try:
            # Collect news articles
            logger.info("Collecting news articles...")
            articles = self.collectors['news'].collect()
            stats['articles_collected'] = len(articles)
            stats['articles_inserted'] = self.db.insert_articles(articles)
            
            # Collect tweets
            logger.info("Collecting tweets...")
            tweets = self.collectors['twitter'].collect()
            stats['tweets_collected'] = len(tweets)
            stats['tweets_inserted'] = self.db.insert_tweets(tweets)
            
            # Collect Google Trends
            logger.info("Collecting Google Trends...")
            trends = self.collectors['google_trends'].collect()
            stats['trends_collected'] = len(trends)
            stats['trends_inserted'] = self.db.insert_google_trends(trends)
            
            # Collect e-commerce sales
            logger.info("Collecting e-commerce data...")
            sales = self.collectors['ecommerce'].collect()
            stats['sales_collected'] = len(sales)
            stats['sales_inserted'] = self.db.insert_ecommerce_sales(sales)
            
            # Collect Reddit posts
            logger.info("Collecting Reddit posts...")
            posts = self.collectors['reddit'].collect()
            stats['posts_collected'] = len(posts)
            stats['posts_inserted'] = self.db.insert_reddit_posts(posts)
            
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            raise
        
        elapsed_time = time.time() - start_time
        
        logger.info("=" * 50)
        logger.info("Pipeline execution completed")
        logger.info(f"Execution time: {elapsed_time:.2f} seconds")
        logger.info(f"Statistics: {stats}")
        logger.info("=" * 50)
        
        return stats


if __name__ == "__main__":
    # Quick test
    db = DatabaseManager(config.DB_PATH)
    db.create_tables()
    
    pipeline = DataPipeline(db)
    pipeline.run_hourly()
    
    print("\n✓ Pipeline test completed successfully!")
    print(f"\nDatabase stats: {db.get_stats()}")
