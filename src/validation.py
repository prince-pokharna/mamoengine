import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationManager:
    """Validate and clean data quality."""

    def __init__(self):
        self.validation_report = {
            'timestamp': None,
            'articles': {'total': 0, 'valid': 0, 'invalid': 0, 'issues': []},
            'tweets': {'total': 0, 'valid': 0, 'invalid': 0, 'issues': []},
            'trends': {'total': 0, 'valid': 0, 'invalid': 0, 'issues': []},
            'ecommerce': {'total': 0, 'valid': 0, 'invalid': 0, 'issues': []},
            'reddit': {'total': 0, 'valid': 0, 'invalid': 0, 'issues': []},
        }

    def validate_article(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate article data."""
        if not data.get('title') or not data['title'].strip():
            return False, "Empty title"

        if not data.get('content') or len(data['content']) < 50:
            return False, "Content too short (< 50 chars)"

        if not data.get('url') or not data['url'].startswith(('http://', 'https://')):
            return False, "Invalid or missing URL"

        if not data.get('published_date'):
            return False, "Missing published_date"

        return True, "Valid"

    def validate_tweet(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate tweet data."""
        if not data.get('text') or not (10 <= len(data['text']) <= 280):
            return False, "Text length not between 10-280 chars"

        if not data.get('created_date'):
            return False, "Missing created_date"

        if not data.get('author') or not data['author'].strip():
            return False, "Empty author"

        return True, "Valid"

    def validate_trend(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Google Trends data."""
        if not data.get('keyword') or not data['keyword'].strip():
            return False, "Empty keyword"

        if not isinstance(data.get('search_volume'), int) or data['search_volume'] <= 0:
            return False, "Invalid search_volume (must be > 0)"

        if not data.get('date'):
            return False, "Missing date"

        return True, "Valid"

    def validate_ecommerce(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate ecommerce data."""
        valid_categories = ["phones", "laptops", "fashion", "home", "food"]

        if data.get('category') not in valid_categories:
            return False, f"Invalid category: {data.get('category')}"

        if not isinstance(data.get('sales_count'), int) or data['sales_count'] <= 0:
            return False, "Invalid sales_count (must be > 0)"

        if not data.get('date'):
            return False, "Missing date"

        if not data.get('region') or not data['region'].strip():
            return False, "Empty region"

        return True, "Valid"

    def validate_reddit(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Reddit post data."""
        if (not data.get('title') or not data['title'].strip()) and (not data.get('text') or not data['text'].strip()):
            return False, "Both title and text are empty"

        if not data.get('subreddit') or not data['subreddit'].strip():
            return False, "Empty subreddit"

        if not data.get('created_date'):
            return False, "Missing created_date"

        return True, "Valid"

    def check_date_ranges(self, data: Dict[str, Any], date_field: str) -> Tuple[bool, str]:
        """Ensure dates are reasonable (not future, not >1 year old)."""
        try:
            if isinstance(data.get(date_field), str):
                date_obj = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))
            else:
                date_obj = data.get(date_field)

            now = datetime.utcnow()
            one_year_ago = now - timedelta(days=365)

            if date_obj > now:
                return False, f"{date_field} is in the future"

            if date_obj < one_year_ago:
                return False, f"{date_field} is more than 1 year old"

            return True, "Date range valid"

        except Exception as e:
            return False, f"Invalid date format: {str(e)}"

    def remove_spam(self, text: str) -> Tuple[bool, str]:
        """Filter obvious spam (all caps, repeated chars, etc.)."""
        if not text or len(text) < 5:
            return False, "Text too short"

        if len(text) > 3000:
            return False, "Text too long"

        all_caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if all_caps_ratio > 0.8:
            return False, "Too much uppercase (spam indicator)"

        if any(text.count(c) > len(text) * 0.3 for c in 'abcdefghijklmnopqrstuvwxyz'):
            return False, "Too many repeated characters (spam indicator)"

        return True, "Not spam"

    def validate_articles_batch(self, articles: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict]:
        """Validate batch of articles."""
        valid_articles = []
        stats = {'total': len(articles), 'valid': 0, 'invalid': 0, 'issues': []}

        for article in articles:
            is_valid, reason = self.validate_article(article)

            if is_valid:
                is_spam, spam_reason = self.remove_spam(article.get('content', ''))
                if not is_spam:
                    is_valid, reason = False, f"Spam detected: {spam_reason}"

            if is_valid:
                is_valid, reason = self.check_date_ranges(article, 'published_date')

            if is_valid:
                valid_articles.append(article)
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
                stats['issues'].append(reason)

        logger.info(f"Article validation: {stats['valid']}/{stats['total']} valid")
        return valid_articles, stats

    def validate_tweets_batch(self, tweets: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict]:
        """Validate batch of tweets."""
        valid_tweets = []
        stats = {'total': len(tweets), 'valid': 0, 'invalid': 0, 'issues': []}

        for tweet in tweets:
            is_valid, reason = self.validate_tweet(tweet)

            if is_valid:
                is_spam, spam_reason = self.remove_spam(tweet.get('text', ''))
                if not is_spam:
                    is_valid, reason = False, f"Spam detected: {spam_reason}"

            if is_valid:
                is_valid, reason = self.check_date_ranges(tweet, 'created_date')

            if is_valid:
                valid_tweets.append(tweet)
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
                stats['issues'].append(reason)

        logger.info(f"Tweet validation: {stats['valid']}/{stats['total']} valid")
        return valid_tweets, stats

    def validate_trends_batch(self, trends: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict]:
        """Validate batch of trends."""
        valid_trends = []
        stats = {'total': len(trends), 'valid': 0, 'invalid': 0, 'issues': []}

        for trend in trends:
            is_valid, reason = self.validate_trend(trend)

            if is_valid:
                is_valid, reason = self.check_date_ranges(trend, 'date')

            if is_valid:
                valid_trends.append(trend)
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
                stats['issues'].append(reason)

        logger.info(f"Trend validation: {stats['valid']}/{stats['total']} valid")
        return valid_trends, stats

    def validate_ecommerce_batch(self, sales: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict]:
        """Validate batch of ecommerce data."""
        valid_sales = []
        stats = {'total': len(sales), 'valid': 0, 'invalid': 0, 'issues': []}

        for sale in sales:
            is_valid, reason = self.validate_ecommerce(sale)

            if is_valid:
                is_valid, reason = self.check_date_ranges(sale, 'date')

            if is_valid:
                valid_sales.append(sale)
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
                stats['issues'].append(reason)

        logger.info(f"Ecommerce validation: {stats['valid']}/{stats['total']} valid")
        return valid_sales, stats

    def validate_reddit_batch(self, posts: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict]:
        """Validate batch of Reddit posts."""
        valid_posts = []
        stats = {'total': len(posts), 'valid': 0, 'invalid': 0, 'issues': []}

        for post in posts:
            is_valid, reason = self.validate_reddit(post)

            if is_valid:
                is_valid, reason = self.check_date_ranges(post, 'created_date')

            if is_valid:
                valid_posts.append(post)
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
                stats['issues'].append(reason)

        logger.info(f"Reddit validation: {stats['valid']}/{stats['total']} valid")
        return valid_posts, stats

    def save_report(self, filepath: str = 'data/validation_report.json'):
        """Save validation report to JSON."""
        self.validation_report['timestamp'] = datetime.utcnow().isoformat()

        with open(filepath, 'w') as f:
            json.dump(self.validation_report, f, indent=2, default=str)

        logger.info(f"Validation report saved to {filepath}")
