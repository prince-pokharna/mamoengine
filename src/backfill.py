import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.database import DatabaseManager
from src.data_ingestion import (
    MockEcommerceCollector,
    MockRedditCollector,
    GoogleTrendsCollector
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackfillCollector:
    """Collect historical data for the past N days."""

    def __init__(self, db_manager: DatabaseManager, days: int = 7):
        self.db = db_manager
        self.days = days
        self.start_date = datetime.utcnow() - timedelta(days=days)

    def backfill_google_trends(self) -> int:
        """Generate historical Google Trends data."""
        trends = []
        keywords = ["OnePlus", "Flipkart", "Amazon India", "new phone", "gadgets"]

        for day_offset in range(self.days):
            date = self.start_date + timedelta(days=day_offset)

            for keyword in keywords:
                search_volume = random.randint(20, 100)
                if day_offset == self.days - 1:
                    search_volume = random.randint(30, 100)

                trends.append({
                    'keyword': keyword,
                    'search_volume': search_volume,
                    'date': date.isoformat(),
                    'category': 'Technology'
                })

        inserted = self.db.insert_google_trends(trends)
        logger.info(f"Backfilled {inserted} Google Trends records")
        return inserted

    def backfill_ecommerce_sales(self) -> int:
        """Generate historical ecommerce sales data."""
        sales = []
        categories = ["phones", "laptops", "fashion", "home", "food"]
        regions = ["North", "South", "East", "West", "Central"]

        for day_offset in range(self.days):
            date = self.start_date + timedelta(days=day_offset)
            is_weekend = date.weekday() >= 5

            for hour_offset in range(0, 24, 4):
                for category in categories:
                    base_sales = random.randint(80, 400)

                    if is_weekend:
                        base_sales = int(base_sales * 1.4)

                    peak_hours = [10, 11, 19, 20, 21, 22]
                    if hour_offset in peak_hours:
                        base_sales = int(base_sales * 1.2)

                    for region in regions:
                        sales.append({
                            'category': category,
                            'sales_count': base_sales + random.randint(-30, 50),
                            'date': (date + timedelta(hours=hour_offset)).isoformat(),
                            'region': region
                        })

        inserted = self.db.insert_ecommerce_sales(sales)
        logger.info(f"Backfilled {inserted} ecommerce sales records")
        return inserted

    def backfill_reddit_posts(self) -> int:
        """Generate historical Reddit posts."""
        posts = []
        subreddits = ["r/india", "r/IndianGaming", "r/BudgetPhones"]

        post_templates = [
            ("Should I buy the new {product}?", "Looking for opinions on the {product}. Is it worth the price?"),
            ("Best deals on {product} right now", "Found some amazing deals on {product} this week"),
            ("{product} review after 1 week", "Been using the {product} for a week now, here are my thoughts"),
            ("Why everyone should consider {product}", "If you're in the market for tech, {product} is worth looking at"),
            ("Anyone else excited about {product}?", "The new {product} release has me really interested"),
            ("Help needed: choosing between {product} options", "I'm confused about which {product} to buy"),
        ]

        products = ["OnePlus", "Samsung", "Laptop", "Phone", "Gadget", "Camera"]

        for day_offset in range(self.days):
            date = self.start_date + timedelta(days=day_offset)

            for post_num in range(random.randint(3, 8)):
                hour = random.randint(0, 23)
                template = random.choice(post_templates)
                product = random.choice(products)

                post_date = date + timedelta(hours=hour, minutes=random.randint(0, 59))

                posts.append({
                    'title': template[0].format(product=product),
                    'text': template[1].format(product=product),
                    'subreddit': random.choice(subreddits),
                    'score': random.randint(5, 300),
                    'created_date': post_date.isoformat()
                })

        inserted = self.db.insert_reddit_posts(posts)
        logger.info(f"Backfilled {inserted} Reddit posts")
        return inserted

    def backfill_mock_articles(self) -> int:
        """Generate realistic historical article data."""
        articles = []

        article_templates = [
            {
                "source": "TechNews",
                "title_template": "New developments in {category}: What you need to know",
                "content_template": "Recent market analysis shows significant growth in the {category} sector. Industry experts predict continued expansion through the rest of the year. Consumer interest remains high with searches for related products up by 40%. Companies are investing heavily in research and development to meet growing demand."
            },
            {
                "source": "MarketReport",
                "title_template": "{category} market reaches new milestone",
                "content_template": "The {category} industry has reached unprecedented levels of consumer engagement. Market research firms report strong sales figures and positive sentiment across all regions. Retailers are expanding their inventories to meet demand. Customer reviews show high satisfaction rates with recent product releases."
            },
            {
                "source": "ConsumerDaily",
                "title_template": "Top trends in {category} this season",
                "content_template": "Analysts have identified key trends driving the {category} market forward. Online retailers report increased traffic and conversion rates. Social media discussions about {category} products have surged by 60%. Early adopters share positive experiences with new offerings in the segment."
            },
        ]

        categories = ["tech", "smartphones", "fashion", "food & beverages", "home appliances"]

        for day_offset in range(self.days):
            date = self.start_date + timedelta(days=day_offset)

            for article_num in range(random.randint(2, 4)):
                template = random.choice(article_templates)
                category = random.choice(categories)

                article_date = date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))

                articles.append({
                    'source': template['source'],
                    'title': template['title_template'].format(category=category),
                    'content': template['content_template'].format(category=category),
                    'published_date': article_date.isoformat(),
                    'fetched_date': datetime.utcnow().isoformat(),
                    'url': f"https://example.com/article/{day_offset}-{article_num}"
                })

        inserted = self.db.insert_articles(articles)
        logger.info(f"Backfilled {inserted} article records")
        return inserted

    def run(self) -> Dict[str, int]:
        """Run complete backfill operation."""
        logger.info(f"=== Starting {self.days}-day historical backfill ===")

        stats = {
            'google_trends': self.backfill_google_trends(),
            'ecommerce_sales': self.backfill_ecommerce_sales(),
            'reddit_posts': self.backfill_reddit_posts(),
            'articles': self.backfill_mock_articles(),
        }

        logger.info("=== Backfill Summary ===")
        for source, count in stats.items():
            logger.info(f"{source}: {count} records")

        return stats


def main():
    """Run backfill operation."""
    db = DatabaseManager('data/market_mood.db')

    logger.info(f"Database path: data/market_mood.db")
    logger.info(f"Existing stats: {db.get_stats()}")

    backfiller = BackfillCollector(db, days=7)
    backfiller.run()

    logger.info(f"Updated stats: {db.get_stats()}")
    logger.info("Backfill completed successfully!")

    db.close()


if __name__ == '__main__':
    main()
