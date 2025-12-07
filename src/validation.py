"""
Data validation module for Market-Mood Engine.
Validates and cleans data before database insertion.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re

from src.models import Article, Tweet, GoogleTrend, EcommerceSale, RedditPost
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationManager:
    """Manages data validation and quality checks."""
    
    def __init__(self):
        self.validation_stats = {
            'articles': {'valid': 0, 'invalid': 0, 'reasons': {}},
            'tweets': {'valid': 0, 'invalid': 0, 'reasons': {}},
            'trends': {'valid': 0, 'invalid': 0, 'reasons': {}},
            'sales': {'valid': 0, 'invalid': 0, 'reasons': {}},
            'reddit': {'valid': 0, 'invalid': 0, 'reasons': {}}
        }
        logger.info("ValidationManager initialized")
    
    def validate_article(self, article: Article) -> tuple[bool, str]:
        """
        Validate article data.
        
        Args:
            article: Article object to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check title not empty
        if not article.title or len(article.title.strip()) < 3:
            return False, "title_too_short"
        
        # Check content minimum length
        if not article.content or len(article.content) < config.MIN_ARTICLE_CONTENT_LENGTH:
            return False, "content_too_short"
        
        # Check URL exists
        if not article.url or len(article.url) < 10:
            return False, "invalid_url"
        
        # Check date is not in future
        if article.published_date > datetime.now() + timedelta(hours=1):
            return False, "future_date"
        
        # Check date is not too old (more than 1 year)
        if article.published_date < datetime.now() - timedelta(days=365):
            return False, "date_too_old"
        
        # Check for spam patterns
        if self._is_spam(article.title) or self._is_spam(article.content):
            return False, "spam_detected"
        
        return True, "valid"
    
    def validate_tweet(self, tweet: Tweet) -> tuple[bool, str]:
        """
        Validate tweet data.
        
        Args:
            tweet: Tweet object to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check text length
        if not tweet.text or len(tweet.text) < config.MIN_TWEET_LENGTH:
            return False, "text_too_short"
        
        if len(tweet.text) > config.MAX_TWEET_LENGTH:
            return False, "text_too_long"
        
        # Check created date exists
        if not tweet.created_date:
            return False, "missing_date"
        
        # Check date is not in future
        if tweet.created_date > datetime.now() + timedelta(hours=1):
            return False, "future_date"
        
        # Check engagement metrics are non-negative
        if tweet.likes < 0 or tweet.retweets < 0:
            return False, "invalid_metrics"
        
        # Check for spam
        if self._is_spam(tweet.text):
            return False, "spam_detected"
        
        return True, "valid"
    
    def validate_trend(self, trend: GoogleTrend) -> tuple[bool, str]:
        """
        Validate Google Trends data.
        
        Args:
            trend: GoogleTrend object to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check keyword exists
        if not trend.keyword or len(trend.keyword.strip()) < 2:
            return False, "invalid_keyword"
        
        # Check search volume is positive
        if trend.search_volume < 0:
            return False, "negative_volume"
        
        # Check date is valid
        if not trend.date:
            return False, "missing_date"
        
        if trend.date > datetime.now() + timedelta(hours=1):
            return False, "future_date"
        
        return True, "valid"
    
    def validate_ecommerce(self, sale: EcommerceSale) -> tuple[bool, str]:
        """
        Validate e-commerce sales data.
        
        Args:
            sale: EcommerceSale object to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check category is valid
        if sale.category not in config.CATEGORIES:
            return False, "invalid_category"
        
        # Check sales count is positive
        if sale.sales_count <= 0:
            return False, "invalid_sales_count"
        
        # Check date is valid
        if not sale.date:
            return False, "missing_date"
        
        if sale.date > datetime.now() + timedelta(hours=1):
            return False, "future_date"
        
        return True, "valid"
    
    def validate_reddit(self, post: RedditPost) -> tuple[bool, str]:
        """
        Validate Reddit post data.
        
        Args:
            post: RedditPost object to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check title not empty
        if not post.title or len(post.title.strip()) < 3:
            return False, "title_too_short"
        
        # Check text not empty
        if not post.text or len(post.text.strip()) < 5:
            return False, "text_too_short"
        
        # Check valid date
        if not post.created_date:
            return False, "missing_date"
        
        if post.created_date > datetime.now() + timedelta(hours=1):
            return False, "future_date"
        
        # Check for spam
        if self._is_spam(post.title) or self._is_spam(post.text):
            return False, "spam_detected"
        
        return True, "valid"
    
    def _is_spam(self, text: str) -> bool:
        """
        Detect spam patterns in text.
        
        Args:
            text: Text to check
            
        Returns:
            True if spam detected, False otherwise
        """
        if not text:
            return True
        
        # Check for all caps (spam indicator)
        if len(text) > 10 and text.isupper():
            return True
        
        # Check for excessive repeated characters
        if re.search(r'(.)\1{5,}', text):
            return True
        
        # Check for excessive exclamation or question marks
        if text.count('!') > 5 or text.count('?') > 5:
            return True
        
        # Check for common spam phrases
        spam_phrases = ['click here', 'buy now', 'limited time', 'act now', 'free money']
        text_lower = text.lower()
        spam_count = sum(1 for phrase in spam_phrases if phrase in text_lower)
        if spam_count >= 2:
            return True
        
        return False
    
    def remove_duplicates(self, items: List[Any], key_func) -> List[Any]:
        """
        Remove duplicate items based on key function.
        
        Args:
            items: List of items to deduplicate
            key_func: Function to extract unique key from item
            
        Returns:
            List of unique items
        """
        seen = set()
        unique_items = []
        
        for item in items:
            try:
                key = key_func(item)
                if key not in seen:
                    seen.add(key)
                    unique_items.append(item)
            except Exception as e:
                logger.error(f"Error extracting key: {e}")
        
        duplicates_removed = len(items) - len(unique_items)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate items")
        
        return unique_items
    
    def validate_articles(self, articles: List[Article]) -> List[Article]:
        """Validate and filter articles."""
        valid_articles = []
        
        for article in articles:
            is_valid, reason = self.validate_article(article)
            
            if is_valid:
                self.validation_stats['articles']['valid'] += 1
                valid_articles.append(article)
            else:
                self.validation_stats['articles']['invalid'] += 1
                self.validation_stats['articles']['reasons'][reason] = \
                    self.validation_stats['articles']['reasons'].get(reason, 0) + 1
        
        return valid_articles
    
    def validate_tweets(self, tweets: List[Tweet]) -> List[Tweet]:
        """Validate and filter tweets."""
        valid_tweets = []
        
        for tweet in tweets:
            is_valid, reason = self.validate_tweet(tweet)
            
            if is_valid:
                self.validation_stats['tweets']['valid'] += 1
                valid_tweets.append(tweet)
            else:
                self.validation_stats['tweets']['invalid'] += 1
                self.validation_stats['tweets']['reasons'][reason] = \
                    self.validation_stats['tweets']['reasons'].get(reason, 0) + 1
        
        return valid_tweets
    
    def validate_trends(self, trends: List[GoogleTrend]) -> List[GoogleTrend]:
        """Validate and filter trends."""
        valid_trends = []
        
        for trend in trends:
            is_valid, reason = self.validate_trend(trend)
            
            if is_valid:
                self.validation_stats['trends']['valid'] += 1
                valid_trends.append(trend)
            else:
                self.validation_stats['trends']['invalid'] += 1
                self.validation_stats['trends']['reasons'][reason] = \
                    self.validation_stats['trends']['reasons'].get(reason, 0) + 1
        
        return valid_trends
    
    def validate_sales(self, sales: List[EcommerceSale]) -> List[EcommerceSale]:
        """Validate and filter sales data."""
        valid_sales = []
        
        for sale in sales:
            is_valid, reason = self.validate_ecommerce(sale)
            
            if is_valid:
                self.validation_stats['sales']['valid'] += 1
                valid_sales.append(sale)
            else:
                self.validation_stats['sales']['invalid'] += 1
                self.validation_stats['sales']['reasons'][reason] = \
                    self.validation_stats['sales']['reasons'].get(reason, 0) + 1
        
        return valid_sales
    
    def validate_reddit_posts(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Validate and filter Reddit posts."""
        valid_posts = []
        
        for post in posts:
            is_valid, reason = self.validate_reddit(post)
            
            if is_valid:
                self.validation_stats['reddit']['valid'] += 1
                valid_posts.append(post)
            else:
                self.validation_stats['reddit']['invalid'] += 1
                self.validation_stats['reddit']['reasons'][reason] = \
                    self.validation_stats['reddit']['reasons'].get(reason, 0) + 1
        
        return valid_posts
    
    def save_validation_report(self, filepath: str = "data/validation_report.json"):
        """
        Save validation statistics to JSON file.
        
        Args:
            filepath: Path to save report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.validation_stats
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Validation report saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get validation summary.
        
        Returns:
            Dictionary with validation statistics
        """
        summary = {}
        for data_type, stats in self.validation_stats.items():
            total = stats['valid'] + stats['invalid']
            if total > 0:
                pass_rate = (stats['valid'] / total) * 100
                summary[data_type] = {
                    'total': total,
                    'valid': stats['valid'],
                    'invalid': stats['invalid'],
                    'pass_rate': f"{pass_rate:.1f}%",
                    'top_issues': dict(sorted(
                        stats['reasons'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:3])
                }
        
        return summary
