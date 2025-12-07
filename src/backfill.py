"""
Historical data backfill script for Market-Mood Engine.
Collects and generates 7 days of historical data for training models.
"""
import logging
import random
from datetime import datetime, timedelta
from typing import List

from src.models import Article, Tweet, GoogleTrend, EcommerceSale, RedditPost
from src.database import DatabaseManager
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackfillCollector:
    """Collects historical data for model training."""
    
    def __init__(self, days: int = 7):
        """
        Initialize backfill collector.
        
        Args:
            days: Number of days of historical data to collect
        """
        self.days = days
        logger.info(f"BackfillCollector initialized for {days} days")
    
    def collect_historical_news(self) -> List[Article]:
        """
        Generate historical news articles.
        
        Returns:
            List of historical articles
        """
        logger.info("Generating historical news articles...")
        
        article_templates = [
            {
                "source": "TechCrunch",
                "title": "New smartphone launch promises innovation",
                "content": "A major tech company unveiled its latest flagship device today with advanced features and competitive pricing. Industry analysts predict strong market performance."
            },
            {
                "source": "Economic Times",
                "title": "E-commerce platforms report growth in festive sales",
                "content": "Major online retailers have seen significant increases in transaction volumes. Consumer electronics and fashion categories led the growth surge across platforms."
            },
            {
                "source": "Fashion Weekly",
                "title": "Sustainable fashion trend continues to grow",
                "content": "Eco-friendly clothing brands are gaining market share as consumers become more environmentally conscious. Sales data shows a consistent upward trend."
            },
            {
                "source": "Food Business",
                "title": "Cloud kitchens expand operations across cities",
                "content": "Food delivery platforms and cloud kitchen operators are opening new locations to meet increasing demand. The model continues to attract investor interest."
            },
            {
                "source": "Startup Digest",
                "title": "Tech startups receive increased funding",
                "content": "Venture capital investments in technology startups reached new highs this quarter. Artificial intelligence and fintech sectors dominated funding rounds."
            },
            {
                "source": "Gadget Review",
                "title": "Consumer interest in smart home devices rises",
                "content": "Smart home technology adoption is accelerating as prices become more accessible. Voice assistants and automated systems lead category growth."
            },
            {
                "source": "Business Today",
                "title": "Online shopping patterns shift post-pandemic",
                "content": "Consumer behavior continues to evolve with hybrid shopping preferences. Data shows balanced growth between online and offline retail channels."
            }
        ]
        
        articles = []
        
        # Generate articles spread across the days
        for day in range(self.days):
            date_offset = timedelta(days=day)
            base_date = datetime.now() - timedelta(days=self.days) + date_offset
            
            # Generate 3-5 articles per day
            articles_per_day = random.randint(3, 5)
            
            for _ in range(articles_per_day):
                template = random.choice(article_templates)
                
                # Add time variation throughout the day
                hour_offset = timedelta(hours=random.randint(0, 23), 
                                       minutes=random.randint(0, 59))
                article_date = base_date + hour_offset
                
                # Add slight variation to content
                variations = [
                    " Market experts remain optimistic about future prospects.",
                    " Consumer sentiment indicates positive market trends.",
                    " Industry watchers predict continued momentum in coming months.",
                    " Early indicators suggest sustained growth trajectory.",
                    " Stakeholders express confidence in market direction."
                ]
                
                content = template["content"] + random.choice(variations)
                
                article = Article(
                    source=template["source"],
                    title=template["title"],
                    content=content,
                    published_date=article_date,
                    url=f"https://example.com/article-{random.randint(10000, 99999)}",
                    fetched_date=datetime.now()
                )
                articles.append(article)
        
        logger.info(f"Generated {len(articles)} historical articles")
        return articles
    
    def collect_historical_tweets(self) -> List[Tweet]:
        """Generate historical tweets."""
        logger.info("Generating historical tweets...")
        
        tweet_templates = [
            "Just got the new phone! The features are incredible {emoji}",
            "Amazing deals on the shopping app today {emoji}",
            "The new gadget is a game changer for productivity",
            "Customer service was exceptional with my recent purchase",
            "Loving the latest tech trends in the market",
            "Best electronics sale I've seen in months",
            "This product exceeded my expectations completely",
            "Great value for money on this purchase",
            "The innovation in this space is remarkable",
            "Highly recommend checking out the new releases"
        ]
        
        emojis = ["📱", "💻", "🎮", "⚡", "🚀", "👍", "✨", "🔥"]
        
        tweets = []
        
        # Generate tweets spread across days
        for day in range(self.days):
            date_offset = timedelta(days=day)
            base_date = datetime.now() - timedelta(days=self.days) + date_offset
            
            # Generate 5-10 tweets per day
            tweets_per_day = random.randint(5, 10)
            
            for _ in range(tweets_per_day):
                template = random.choice(tweet_templates)
                emoji = random.choice(emojis)
                text = template.replace("{emoji}", emoji)
                
                # Add time variation
                time_offset = timedelta(hours=random.randint(0, 23),
                                       minutes=random.randint(0, 59))
                tweet_date = base_date + time_offset
                
                # Older tweets have slightly lower engagement
                recency_factor = 1.0 - (day * 0.1)
                
                tweet = Tweet(
                    text=text,
                    author=f"user_{random.randint(1000, 9999)}",
                    created_date=tweet_date,
                    likes=int(random.randint(10, 100) * recency_factor),
                    retweets=int(random.randint(2, 30) * recency_factor),
                    source_name='twitter',
                    fetched_date=datetime.now()
                )
                tweets.append(tweet)
        
        logger.info(f"Generated {len(tweets)} historical tweets")
        return tweets
    
    def collect_historical_google_trends(self) -> List[GoogleTrend]:
        """Generate historical Google Trends data."""
        logger.info("Generating historical Google Trends...")
        
        keywords = ["OnePlus", "iPhone", "Amazon India", "Flipkart", "laptops", 
                   "smartphones", "gadgets", "fashion"]
        
        trends = []
        
        # Generate daily trends
        for day in range(self.days):
            date_offset = timedelta(days=day)
            trend_date = datetime.now() - timedelta(days=self.days) + date_offset
            
            for keyword in keywords:
                # Generate realistic search volumes with some trend
                base_volume = random.randint(60, 90)
                trend_factor = 1.0 + (day * 0.05)  # Slight upward trend
                noise = random.uniform(0.9, 1.1)
                search_volume = int(base_volume * trend_factor * noise)
                
                trend = GoogleTrend(
                    keyword=keyword,
                    search_volume=search_volume,
                    date=trend_date,
                    category='technology',
                    fetched_date=datetime.now()
                )
                trends.append(trend)
        
        logger.info(f"Generated {len(trends)} historical trends")
        return trends
    
    def collect_historical_ecommerce(self) -> List[EcommerceSale]:
        """Generate historical e-commerce sales data."""
        logger.info("Generating historical e-commerce data...")
        
        categories = config.CATEGORIES
        base_sales = {
            "phones": 5000,
            "laptops": 2000,
            "fashion": 8000,
            "home": 3000,
            "food": 12000
        }
        
        sales = []
        
        # Generate daily sales data
        for day in range(self.days):
            date_offset = timedelta(days=day)
            sale_date = datetime.now() - timedelta(days=self.days) + date_offset
            
            # Weekend boost
            is_weekend = sale_date.weekday() >= 5
            weekend_factor = 1.5 if is_weekend else 1.0
            
            # Growing trend
            growth_factor = 1.0 + (day * 0.02)
            
            for category in categories:
                base = base_sales.get(category, 1000)
                variance = random.uniform(0.85, 1.15)
                sales_count = int(base * weekend_factor * growth_factor * variance)
                
                sale = EcommerceSale(
                    category=category,
                    sales_count=sales_count,
                    date=sale_date,
                    region="India",
                    fetched_date=datetime.now()
                )
                sales.append(sale)
        
        logger.info(f"Generated {len(sales)} historical sales records")
        return sales
    
    def collect_historical_reddit(self) -> List[RedditPost]:
        """Generate historical Reddit posts."""
        logger.info("Generating historical Reddit posts...")
        
        post_templates = [
            {
                "subreddit": "india",
                "title": "What are your thoughts on the latest phone releases?",
                "text": "Looking for opinions on which new smartphone offers the best value for money."
            },
            {
                "subreddit": "IndianGaming",
                "title": "Gaming laptop recommendations needed",
                "text": "Budget is flexible, looking for something that can handle modern games well."
            },
            {
                "subreddit": "BudgetPhones",
                "title": "Comparison between mid-range options",
                "text": "Trying to decide between several models in the 15-25k range."
            },
            {
                "subreddit": "india",
                "title": "E-commerce sales experience thread",
                "text": "Share your recent shopping experiences and deals you found."
            },
            {
                "subreddit": "IndianGaming",
                "title": "Best accessories for gaming setup",
                "text": "What peripherals and accessories do you recommend?"
            }
        ]
        
        posts = []
        
        # Generate posts spread across days
        for day in range(self.days):
            date_offset = timedelta(days=day)
            base_date = datetime.now() - timedelta(days=self.days) + date_offset
            
            # Generate 2-4 posts per day
            posts_per_day = random.randint(2, 4)
            
            for _ in range(posts_per_day):
                template = random.choice(post_templates)
                
                # Add time variation
                time_offset = timedelta(hours=random.randint(0, 23),
                                       minutes=random.randint(0, 59))
                post_date = base_date + time_offset
                
                # Older posts accumulate more score
                age_factor = 1.0 + (day * 0.3)
                
                post = RedditPost(
                    title=template["title"],
                    text=template["text"],
                    subreddit=template["subreddit"],
                    score=int(random.randint(10, 100) * age_factor),
                    created_date=post_date,
                    fetched_date=datetime.now()
                )
                posts.append(post)
        
        logger.info(f"Generated {len(posts)} historical Reddit posts")
        return posts
    
    def run_backfill(self, db: DatabaseManager):
        """
        Execute complete backfill process.
        
        Args:
            db: DatabaseManager instance
        """
        logger.info("=" * 60)
        logger.info(f"Starting historical data backfill - {self.days} days")
        logger.info("=" * 60)
        
        # Collect all historical data
        articles = self.collect_historical_news()
        tweets = self.collect_historical_tweets()
        trends = self.collect_historical_google_trends()
        sales = self.collect_historical_ecommerce()
        posts = self.collect_historical_reddit()
        
        # Insert into database
        logger.info("Inserting historical data into database...")
        
        articles_inserted = db.insert_articles(articles)
        tweets_inserted = db.insert_tweets(tweets)
        trends_inserted = db.insert_google_trends(trends)
        sales_inserted = db.insert_ecommerce_sales(sales)
        posts_inserted = db.insert_reddit_posts(posts)
        
        logger.info("=" * 60)
        logger.info("Backfill completed successfully")
        logger.info("=" * 60)
        logger.info(f"Articles inserted: {articles_inserted}/{len(articles)}")
        logger.info(f"Tweets inserted: {tweets_inserted}/{len(tweets)}")
        logger.info(f"Trends inserted: {trends_inserted}/{len(trends)}")
        logger.info(f"Sales records inserted: {sales_inserted}/{len(sales)}")
        logger.info(f"Reddit posts inserted: {posts_inserted}/{len(posts)}")
        logger.info("=" * 60)


if __name__ == "__main__":
    # Run backfill
    db = DatabaseManager(config.DB_PATH)
    db.create_tables()
    
    backfill = BackfillCollector(days=7)
    backfill.run_backfill(db)
    
    # Show statistics
    stats = db.get_stats()
    print("\nDatabase statistics after backfill:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
