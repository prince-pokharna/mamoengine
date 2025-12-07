"""
Sentiment processor for Market-Mood Engine.
Integrates sentiment analysis with database operations.
"""
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.sentiment_analyzer import SentimentAnalyzer
from src.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentProcessor:
    """
    Processes articles/tweets from database and updates with sentiment scores.
    """
    
    def __init__(self, db: DatabaseManager, analyzer: Optional[SentimentAnalyzer] = None):
        """
        Initialize sentiment processor.
        
        Args:
            db: DatabaseManager instance
            analyzer: SentimentAnalyzer instance (creates new if None)
        """
        self.db = db
        self.analyzer = analyzer if analyzer else SentimentAnalyzer()
        logger.info("SentimentProcessor initialized")
    
    def process_pending_articles(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Process articles that don't have sentiment scores yet.
        
        Args:
            limit: Maximum number of articles to process (None for all)
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info("Processing pending articles...")
        
        # Get articles without sentiment scores
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT id, title, content FROM articles WHERE sentiment_score IS NULL"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            articles = cursor.fetchall()
        
        if not articles:
            logger.info("No pending articles to process")
            return {
                "processed": 0,
                "failed": 0,
                "avg_sentiment": 0.0
            }
        
        logger.info(f"Found {len(articles)} articles to process")
        
        processed_count = 0
        failed_count = 0
        sentiments = []
        
        # Process each article
        for article in articles:
            article_id = article['id']
            title = article['title']
            content = article['content']
            
            # Combine title and content for analysis
            full_text = f"{title}. {content}"
            
            try:
                # Analyze sentiment
                result = self.analyzer.analyze(full_text)
                
                # Update database
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE articles 
                        SET sentiment_score = ?, 
                            sentiment_emotion = ?,
                            processed_at = ?
                        WHERE id = ?
                    """, (
                        result['overall_sentiment'],
                        json.dumps(result['emotion']),
                        datetime.now(),
                        article_id
                    ))
                
                processed_count += 1
                sentiments.append(result['overall_sentiment'])
                
                if processed_count % 10 == 0:
                    logger.info(f"Processed {processed_count}/{len(articles)} articles")
                
            except Exception as e:
                logger.error(f"Error processing article {article_id}: {e}")
                failed_count += 1
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        stats = {
            "processed": processed_count,
            "failed": failed_count,
            "avg_sentiment": round(avg_sentiment, 3),
            "positive_count": sum(1 for s in sentiments if s > 0.3),
            "negative_count": sum(1 for s in sentiments if s < -0.3),
            "neutral_count": sum(1 for s in sentiments if -0.3 <= s <= 0.3)
        }
        
        logger.info(f"Processing complete: {stats}")
        return stats
    
    def process_article_batch(self, article_ids: List[int]) -> Dict[str, Any]:
        """
        Process specific articles by ID.
        
        Args:
            article_ids: List of article IDs to process
            
        Returns:
            Processing statistics
        """
        if not article_ids:
            return {"processed": 0, "failed": 0}
        
        logger.info(f"Processing {len(article_ids)} specific articles")
        
        processed_count = 0
        failed_count = 0
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            for article_id in article_ids:
                try:
                    cursor.execute("""
                        SELECT id, title, content FROM articles WHERE id = ?
                    """, (article_id,))
                    
                    article = cursor.fetchone()
                    if not article:
                        logger.warning(f"Article {article_id} not found")
                        failed_count += 1
                        continue
                    
                    # Analyze
                    full_text = f"{article['title']}. {article['content']}"
                    result = self.analyzer.analyze(full_text)
                    
                    # Update
                    cursor.execute("""
                        UPDATE articles 
                        SET sentiment_score = ?, 
                            sentiment_emotion = ?,
                            processed_at = ?
                        WHERE id = ?
                    """, (
                        result['overall_sentiment'],
                        json.dumps(result['emotion']),
                        datetime.now(),
                        article_id
                    ))
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing article {article_id}: {e}")
                    failed_count += 1
        
        logger.info(f"Batch processing complete: {processed_count} processed, {failed_count} failed")
        return {"processed": processed_count, "failed": failed_count}
    
    def get_sentiment_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get sentiment statistics for recent articles.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Sentiment statistics
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get articles with sentiment
            cursor.execute("""
                SELECT sentiment_score, sentiment_emotion, published_date
                FROM articles 
                WHERE sentiment_score IS NOT NULL 
                  AND fetched_date >= ?
                ORDER BY published_date DESC
            """, (cutoff_time,))
            
            articles = cursor.fetchall()
        
        if not articles:
            return {
                "count": 0,
                "avg_sentiment": 0.0,
                "trend": "stable"
            }
        
        # Calculate statistics
        sentiments = [article['sentiment_score'] for article in articles]
        
        positive_count = sum(1 for s in sentiments if s > 0.3)
        negative_count = sum(1 for s in sentiments if s < -0.3)
        neutral_count = len(sentiments) - positive_count - negative_count
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Calculate trend
        if len(sentiments) >= 5:
            recent_half = sentiments[:len(sentiments)//2]
            older_half = sentiments[len(sentiments)//2:]
            
            recent_avg = sum(recent_half) / len(recent_half)
            older_avg = sum(older_half) / len(older_half)
            
            diff = recent_avg - older_avg
            
            if diff > 0.1:
                trend = "improving"
            elif diff < -0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return {
            "count": len(articles),
            "avg_sentiment": round(avg_sentiment, 3),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_percentage": round(positive_count / len(sentiments) * 100, 1),
            "negative_percentage": round(negative_count / len(sentiments) * 100, 1),
            "neutral_percentage": round(neutral_count / len(sentiments) * 100, 1),
            "trend": trend,
            "time_range_hours": hours
        }
    
    def get_sentiment_by_source(self) -> Dict[str, Dict[str, float]]:
        """
        Get average sentiment grouped by source.
        
        Returns:
            Dictionary mapping source to sentiment stats
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT source, 
                       AVG(sentiment_score) as avg_sentiment,
                       COUNT(*) as count
                FROM articles 
                WHERE sentiment_score IS NOT NULL
                GROUP BY source
                ORDER BY avg_sentiment DESC
            """)
            
            results = cursor.fetchall()
        
        source_stats = {}
        for row in results:
            source_stats[row['source']] = {
                "avg_sentiment": round(row['avg_sentiment'], 3),
                "article_count": row['count']
            }
        
        return source_stats
    
    def get_top_positive_articles(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top positive articles."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT title, content, sentiment_score, source, published_date
                FROM articles 
                WHERE sentiment_score IS NOT NULL
                ORDER BY sentiment_score DESC
                LIMIT ?
            """, (limit,))
            
            articles = cursor.fetchall()
        
        return [dict(article) for article in articles]
    
    def get_top_negative_articles(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top negative articles."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT title, content, sentiment_score, source, published_date
                FROM articles 
                WHERE sentiment_score IS NOT NULL
                ORDER BY sentiment_score ASC
                LIMIT ?
            """, (limit,))
            
            articles = cursor.fetchall()
        
        return [dict(article) for article in articles]


if __name__ == "__main__":
    # Test sentiment processor
    import config
    
    print("=" * 60)
    print("SENTIMENT PROCESSOR TEST")
    print("=" * 60)
    
    # Initialize
    db = DatabaseManager(config.DB_PATH)
    processor = SentimentProcessor(db)
    
    # Process pending articles
    print("\nProcessing pending articles...")
    stats = processor.process_pending_articles()
    
    print("\nProcessing Statistics:")
    print(f"  Processed: {stats['processed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Average Sentiment: {stats['avg_sentiment']}")
    print(f"  Positive: {stats.get('positive_count', 0)}")
    print(f"  Negative: {stats.get('negative_count', 0)}")
    print(f"  Neutral: {stats.get('neutral_count', 0)}")
    
    # Get sentiment statistics
    print("\n" + "=" * 60)
    print("SENTIMENT STATISTICS (Last 24 hours)")
    print("=" * 60)
    sentiment_stats = processor.get_sentiment_statistics(hours=24)
    
    for key, value in sentiment_stats.items():
        print(f"  {key}: {value}")
    
    # Get sentiment by source
    print("\n" + "=" * 60)
    print("SENTIMENT BY SOURCE")
    print("=" * 60)
    source_stats = processor.get_sentiment_by_source()
    
    for source, stats in source_stats.items():
        print(f"  {source}: {stats['avg_sentiment']} ({stats['article_count']} articles)")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

