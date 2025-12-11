"""
Database manager for Market-Mood Engine using SQLite.
Handles all database operations including table creation, inserts, queries, and maintenance.
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import json

from src.models import Article, Tweet, GoogleTrend, EcommerceSale, RedditPost

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for market mood data."""
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        logger.info(f"DatabaseManager initialized with path: {db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with WAL mode for concurrent access."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent access (as per developer guide)
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def create_tables(self):
        """Create all required database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    published_date TIMESTAMP NOT NULL,
                    fetched_date TIMESTAMP NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    sentiment_score REAL,
                    sentiment_emotion TEXT,
                    processed_at TIMESTAMP
                )
            """)
            
            # Tweets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tweets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    author TEXT NOT NULL,
                    created_date TIMESTAMP NOT NULL,
                    likes INTEGER DEFAULT 0,
                    retweets INTEGER DEFAULT 0,
                    source_name TEXT DEFAULT 'twitter',
                    fetched_date TIMESTAMP NOT NULL,
                    UNIQUE(text, author, created_date)
                )
            """)
            
            # Google Trends table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS google_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    search_volume INTEGER NOT NULL,
                    date TIMESTAMP NOT NULL,
                    category TEXT,
                    fetched_date TIMESTAMP NOT NULL,
                    UNIQUE(keyword, date)
                )
            """)
            
            # E-commerce Sales table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ecommerce_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    sales_count INTEGER NOT NULL,
                    date TIMESTAMP NOT NULL,
                    region TEXT DEFAULT 'India',
                    fetched_date TIMESTAMP NOT NULL,
                    UNIQUE(category, date, region)
                )
            """)
            
            # Reddit Posts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reddit_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    subreddit TEXT NOT NULL,
                    score INTEGER DEFAULT 0,
                    created_date TIMESTAMP NOT NULL,
                    fetched_date TIMESTAMP NOT NULL,
                    UNIQUE(title, subreddit, created_date)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_created ON tweets(created_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_date ON google_trends(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON ecommerce_sales(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reddit_created ON reddit_posts(created_date)")
            
            logger.info("All database tables created successfully")
    
    def insert_articles(self, articles: List[Article]) -> int:
        """
        Batch insert articles into database.
        
        Args:
            articles: List of Article objects
            
        Returns:
            Number of articles inserted
        """
        if not articles:
            return 0
        
        inserted_count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for article in articles:
                try:
                    cursor.execute("""
                        INSERT INTO articles (source, title, content, published_date, 
                                            fetched_date, url, sentiment_score, 
                                            sentiment_emotion, processed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article.source,
                        article.title,
                        article.content,
                        article.published_date,
                        article.fetched_date,
                        article.url,
                        article.sentiment_score,
                        article.sentiment_emotion,
                        article.processed_at
                    ))
                    inserted_count += 1
                except sqlite3.IntegrityError:
                    logger.debug(f"Duplicate article skipped: {article.url}")
                except Exception as e:
                    logger.error(f"Error inserting article: {e}")
        
        logger.info(f"Inserted {inserted_count} articles")
        return inserted_count
    
    def insert_tweets(self, tweets: List[Tweet]) -> int:
        """
        Batch insert tweets into database.
        
        Args:
            tweets: List of Tweet objects
            
        Returns:
            Number of tweets inserted
        """
        if not tweets:
            return 0
        
        inserted_count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for tweet in tweets:
                try:
                    cursor.execute("""
                        INSERT INTO tweets (text, author, created_date, likes, 
                                          retweets, source_name, fetched_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        tweet.text,
                        tweet.author,
                        tweet.created_date,
                        tweet.likes,
                        tweet.retweets,
                        tweet.source_name,
                        tweet.fetched_date
                    ))
                    inserted_count += 1
                except sqlite3.IntegrityError:
                    logger.debug(f"Duplicate tweet skipped")
                except Exception as e:
                    logger.error(f"Error inserting tweet: {e}")
        
        logger.info(f"Inserted {inserted_count} tweets")
        return inserted_count
    
    def insert_google_trends(self, trends: List[GoogleTrend]) -> int:
        """Batch insert Google Trends data."""
        if not trends:
            return 0
        
        inserted_count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for trend in trends:
                try:
                    cursor.execute("""
                        INSERT INTO google_trends (keyword, search_volume, date, 
                                                  category, fetched_date)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        trend.keyword,
                        trend.search_volume,
                        trend.date,
                        trend.category,
                        trend.fetched_date
                    ))
                    inserted_count += 1
                except sqlite3.IntegrityError:
                    logger.debug(f"Duplicate trend skipped: {trend.keyword}")
                except Exception as e:
                    logger.error(f"Error inserting trend: {e}")
        
        logger.info(f"Inserted {inserted_count} trends")
        return inserted_count
    
    def insert_ecommerce_sales(self, sales: List[EcommerceSale]) -> int:
        """Batch insert e-commerce sales data."""
        if not sales:
            return 0
        
        inserted_count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for sale in sales:
                try:
                    cursor.execute("""
                        INSERT INTO ecommerce_sales (category, sales_count, date, 
                                                    region, fetched_date)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        sale.category,
                        sale.sales_count,
                        sale.date,
                        sale.region,
                        sale.fetched_date
                    ))
                    inserted_count += 1
                except sqlite3.IntegrityError:
                    logger.debug(f"Duplicate sale skipped: {sale.category}")
                except Exception as e:
                    logger.error(f"Error inserting sale: {e}")
        
        logger.info(f"Inserted {inserted_count} sales records")
        return inserted_count
    
    def insert_reddit_posts(self, posts: List[RedditPost]) -> int:
        """Batch insert Reddit posts."""
        if not posts:
            return 0
        
        inserted_count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for post in posts:
                try:
                    cursor.execute("""
                        INSERT INTO reddit_posts (title, text, subreddit, score, 
                                                created_date, fetched_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        post.title,
                        post.text,
                        post.subreddit,
                        post.score,
                        post.created_date,
                        post.fetched_date
                    ))
                    inserted_count += 1
                except sqlite3.IntegrityError:
                    logger.debug(f"Duplicate post skipped: {post.title}")
                except Exception as e:
                    logger.error(f"Error inserting post: {e}")
        
        logger.info(f"Inserted {inserted_count} Reddit posts")
        return inserted_count
    
    def get_recent_data(self, hours: int = 24) -> Dict[str, List[Dict]]:
        """
        Fetch recent data from all tables.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with lists of records from each table
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get recent articles
            cursor.execute("""
                SELECT * FROM articles 
                WHERE fetched_date >= ? 
                ORDER BY published_date DESC
            """, (cutoff_time,))
            articles = [dict(row) for row in cursor.fetchall()]
            
            # Get recent tweets
            cursor.execute("""
                SELECT * FROM tweets 
                WHERE fetched_date >= ? 
                ORDER BY created_date DESC
            """, (cutoff_time,))
            tweets = [dict(row) for row in cursor.fetchall()]
            
            # Get recent trends
            cursor.execute("""
                SELECT * FROM google_trends 
                WHERE fetched_date >= ? 
                ORDER BY date DESC
            """, (cutoff_time,))
            trends = [dict(row) for row in cursor.fetchall()]
            
            # Get recent sales
            cursor.execute("""
                SELECT * FROM ecommerce_sales 
                WHERE fetched_date >= ? 
                ORDER BY date DESC
            """, (cutoff_time,))
            sales = [dict(row) for row in cursor.fetchall()]
            
            # Get recent Reddit posts
            cursor.execute("""
                SELECT * FROM reddit_posts 
                WHERE fetched_date >= ? 
                ORDER BY created_date DESC
            """, (cutoff_time,))
            posts = [dict(row) for row in cursor.fetchall()]
        
        logger.info(f"Fetched data from last {hours} hours")
        return {
            'articles': articles,
            'tweets': tweets,
            'trends': trends,
            'sales': sales,
            'reddit_posts': posts
        }
    
    def clean_old_data(self, days: int = 90):
        """
        Remove data older than specified days.
        
        Args:
            days: Number of days to retain
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            tables = ['articles', 'tweets', 'google_trends', 'ecommerce_sales', 'reddit_posts']
            date_columns = ['fetched_date', 'fetched_date', 'fetched_date', 'fetched_date', 'fetched_date']
            
            for table, date_col in zip(tables, date_columns):
                cursor.execute(f"DELETE FROM {table} WHERE {date_col} < ?", (cutoff_date,))
                deleted = cursor.rowcount
                logger.info(f"Deleted {deleted} old records from {table}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts and last update times
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Article stats
            cursor.execute("SELECT COUNT(*) FROM articles")
            stats['articles'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(fetched_date) FROM articles")
            stats['last_article_fetch'] = cursor.fetchone()[0]
            
            # Tweet stats
            cursor.execute("SELECT COUNT(*) FROM tweets")
            stats['tweets'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(fetched_date) FROM tweets")
            stats['last_tweet_fetch'] = cursor.fetchone()[0]
            
            # Trends stats
            cursor.execute("SELECT COUNT(*) FROM google_trends")
            stats['trends'] = cursor.fetchone()[0]
            
            # Sales stats
            cursor.execute("SELECT COUNT(*) FROM ecommerce_sales")
            stats['sales'] = cursor.fetchone()[0]
            
            # Reddit stats
            cursor.execute("SELECT COUNT(*) FROM reddit_posts")
            stats['reddit_posts'] = cursor.fetchone()[0]
        
        logger.info(f"Database stats: {stats}")
        return stats
