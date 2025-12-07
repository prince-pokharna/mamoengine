"""
Trend detection engine for Market-Mood.
Detects emerging trends through sentiment velocity and cross-source validation.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import math

from src.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrendDetector:
    """
    Detects emerging market trends using sentiment velocity, growth rates,
    and cross-source validation.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize trend detector.
        
        Args:
            db: DatabaseManager instance
        """
        self.db = db
        logger.info("TrendDetector initialized")
    
    def detect_trends(self, window_hours: int = 48) -> List[Dict[str, Any]]:
        """
        Detect emerging trends from recent data.
        
        Args:
            window_hours: Time window to analyze (default 48 hours)
            
        Returns:
            List of detected trends with strength scores
        """
        logger.info(f"Detecting trends in {window_hours} hour window")
        
        # Get keywords from articles and tweets
        keywords = self._extract_keywords(window_hours)
        
        if not keywords:
            logger.warning("No keywords found for trend detection")
            return []
        
        trends = []
        
        for keyword, data in keywords.items():
            # Calculate metrics
            velocity = self.get_trend_velocity(keyword, window_hours)
            growth_rate = self.get_growth_rate(keyword, window_hours)
            cross_source_count = data['sources']
            mention_count = data['mentions']
            avg_sentiment = data['avg_sentiment']
            
            # Calculate trend strength
            strength = self.score_trend(
                velocity=velocity,
                growth_rate=growth_rate,
                cross_source_count=cross_source_count,
                mention_count=mention_count
            )
            
            # Determine signal
            signal = self._classify_trend(strength, velocity)
            
            trend = {
                "keyword": keyword,
                "strength": round(strength, 2),
                "velocity": round(velocity, 3),
                "growth_rate": round(growth_rate, 1),
                "sources": list(data['source_list']),
                "mention_count": mention_count,
                "avg_sentiment": round(avg_sentiment, 3),
                "signal": signal,
                "detected_at": datetime.now().isoformat()
            }
            
            trends.append(trend)
        
        # Sort by strength descending
        trends.sort(key=lambda x: x['strength'], reverse=True)
        
        logger.info(f"Detected {len(trends)} trends")
        return trends
    
    def _extract_keywords(self, window_hours: int) -> Dict[str, Dict[str, Any]]:
        """
        Extract keywords and their statistics from recent data.
        
        Args:
            window_hours: Time window to analyze
            
        Returns:
            Dictionary mapping keywords to their statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        
        keywords = defaultdict(lambda: {
            'mentions': 0,
            'sources': 0,
            'source_list': set(),
            'sentiments': []
        })
        
        # Define keywords to track
        tracked_keywords = [
            'iPhone', 'OnePlus', 'Samsung', 'Xiaomi', 'Realme',
            'Amazon', 'Flipkart', 'laptop', 'phone', 'smartphone',
            'gadget', 'fashion', 'ecommerce', 'sale', 'discount'
        ]
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get articles
            cursor.execute("""
                SELECT title, content, source, sentiment_score
                FROM articles
                WHERE fetched_date >= ?
                  AND sentiment_score IS NOT NULL
            """, (cutoff_time,))
            
            articles = cursor.fetchall()
            
            for article in articles:
                text = f"{article['title']} {article['content']}".lower()
                
                for keyword in tracked_keywords:
                    if keyword.lower() in text:
                        keywords[keyword]['mentions'] += 1
                        keywords[keyword]['source_list'].add('news')
                        if article['sentiment_score'] is not None:
                            keywords[keyword]['sentiments'].append(article['sentiment_score'])
            
            # Get tweets
            cursor.execute("""
                SELECT text, created_date
                FROM tweets
                WHERE fetched_date >= ?
            """, (cutoff_time,))
            
            tweets = cursor.fetchall()
            
            for tweet in tweets:
                text = tweet['text'].lower()
                
                for keyword in tracked_keywords:
                    if keyword.lower() in text:
                        keywords[keyword]['mentions'] += 1
                        keywords[keyword]['source_list'].add('twitter')
            
            # Get Google Trends
            cursor.execute("""
                SELECT keyword, search_volume
                FROM google_trends
                WHERE fetched_date >= ?
            """, (cutoff_time,))
            
            trends = cursor.fetchall()
            
            for trend in trends:
                keyword = trend['keyword']
                if keyword in tracked_keywords:
                    keywords[keyword]['mentions'] += trend['search_volume'] // 10
                    keywords[keyword]['source_list'].add('google_trends')
        
        # Calculate averages and counts
        processed_keywords = {}
        for keyword, data in keywords.items():
            if data['mentions'] > 0:
                processed_keywords[keyword] = {
                    'mentions': data['mentions'],
                    'sources': len(data['source_list']),
                    'source_list': data['source_list'],
                    'avg_sentiment': sum(data['sentiments']) / len(data['sentiments']) 
                                    if data['sentiments'] else 0.0
                }
        
        return processed_keywords
    
    def get_trend_velocity(self, keyword: str, window_hours: int = 48) -> float:
        """
        Calculate sentiment velocity for a keyword.
        Velocity = (sentiment_recent - sentiment_older) / sentiment_older
        
        Args:
            keyword: Keyword to analyze
            window_hours: Time window
            
        Returns:
            Velocity score (can be negative)
        """
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        midpoint = datetime.now() - timedelta(hours=window_hours // 2)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get recent sentiment (last half of window)
            cursor.execute("""
                SELECT AVG(sentiment_score) as avg_sentiment
                FROM articles
                WHERE (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)
                  AND sentiment_score IS NOT NULL
                  AND fetched_date >= ?
            """, (f'%{keyword.lower()}%', f'%{keyword.lower()}%', midpoint))
            
            recent_result = cursor.fetchone()
            recent_sentiment = recent_result['avg_sentiment'] if recent_result and recent_result['avg_sentiment'] else 0.0
            
            # Get older sentiment (first half of window)
            cursor.execute("""
                SELECT AVG(sentiment_score) as avg_sentiment
                FROM articles
                WHERE (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)
                  AND sentiment_score IS NOT NULL
                  AND fetched_date >= ?
                  AND fetched_date < ?
            """, (f'%{keyword.lower()}%', f'%{keyword.lower()}%', cutoff_time, midpoint))
            
            older_result = cursor.fetchone()
            older_sentiment = older_result['avg_sentiment'] if older_result and older_result['avg_sentiment'] else 0.0
        
        # Calculate velocity
        if older_sentiment == 0:
            if recent_sentiment > 0:
                return 1.0
            elif recent_sentiment < 0:
                return -1.0
            else:
                return 0.0
        
        velocity = (recent_sentiment - older_sentiment) / abs(older_sentiment)
        return velocity
    
    def get_growth_rate(self, keyword: str, window_hours: int = 48) -> float:
        """
        Calculate mention growth rate.
        Growth = (mentions_recent - mentions_older) / mentions_older * 100
        
        Args:
            keyword: Keyword to analyze
            window_hours: Time window
            
        Returns:
            Growth rate percentage
        """
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        midpoint = datetime.now() - timedelta(hours=window_hours // 2)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get recent mentions
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM articles
                WHERE (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)
                  AND fetched_date >= ?
            """, (f'%{keyword.lower()}%', f'%{keyword.lower()}%', midpoint))
            
            recent_count = cursor.fetchone()['count']
            
            # Get older mentions
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM articles
                WHERE (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)
                  AND fetched_date >= ?
                  AND fetched_date < ?
            """, (f'%{keyword.lower()}%', f'%{keyword.lower()}%', cutoff_time, midpoint))
            
            older_count = cursor.fetchone()['count']
        
        # Calculate growth rate
        if older_count == 0:
            return 100.0 if recent_count > 0 else 0.0
        
        growth_rate = ((recent_count - older_count) / older_count) * 100
        return growth_rate
    
    def score_trend(self, velocity: float, growth_rate: float, 
                   cross_source_count: int, mention_count: int) -> float:
        """
        Calculate overall trend strength score.
        
        Formula: strength = sqrt(velocity^2 * growth_rate_factor * cross_source_weight) * mention_factor
        
        Args:
            velocity: Sentiment velocity
            growth_rate: Mention growth rate percentage
            cross_source_count: Number of sources mentioning trend
            mention_count: Total mentions
            
        Returns:
            Strength score (0-100)
        """
        # Normalize growth rate (0-1 scale)
        growth_factor = min(abs(growth_rate) / 100, 2.0)
        
        # Cross-source weight (more sources = stronger signal)
        cross_source_weight = min(cross_source_count / 3, 1.5)
        
        # Mention factor (more mentions = stronger, but with diminishing returns)
        mention_factor = math.log(mention_count + 1) / math.log(100)
        mention_factor = min(mention_factor, 1.5)
        
        # Calculate base strength
        base_strength = math.sqrt(
            abs(velocity) * growth_factor * cross_source_weight
        ) * mention_factor
        
        # Scale to 0-100
        strength = min(base_strength * 50, 100)
        
        return strength
    
    def _classify_trend(self, strength: float, velocity: float) -> str:
        """
        Classify trend signal based on strength and velocity.
        
        Args:
            strength: Trend strength score
            velocity: Sentiment velocity
            
        Returns:
            Signal classification string
        """
        if strength > 70:
            if velocity > 0:
                return "STRONG EMERGING TREND (POSITIVE)"
            else:
                return "STRONG EMERGING TREND (NEGATIVE)"
        elif strength > 50:
            if velocity > 0:
                return "MODERATE TREND (POSITIVE)"
            else:
                return "MODERATE TREND (NEGATIVE)"
        elif strength > 30:
            return "WEAK TREND"
        else:
            return "STABLE / NO TREND"
    
    def check_cross_source_agreement(self, keyword: str, hours: int = 24) -> Dict[str, Any]:
        """
        Check if trend appears across multiple sources.
        
        Args:
            keyword: Keyword to check
            hours: Time window
            
        Returns:
            Dictionary with cross-source analysis
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        sources = {
            'news': 0,
            'twitter': 0,
            'google_trends': 0
        }
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check news
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM articles
                WHERE (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)
                  AND fetched_date >= ?
            """, (f'%{keyword.lower()}%', f'%{keyword.lower()}%', cutoff_time))
            
            sources['news'] = cursor.fetchone()['count']
            
            # Check tweets
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM tweets
                WHERE LOWER(text) LIKE ?
                  AND fetched_date >= ?
            """, (f'%{keyword.lower()}%', cutoff_time))
            
            sources['twitter'] = cursor.fetchone()['count']
            
            # Check Google Trends
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM google_trends
                WHERE LOWER(keyword) = ?
                  AND fetched_date >= ?
            """, (keyword.lower(), cutoff_time))
            
            sources['google_trends'] = cursor.fetchone()['count']
        
        source_count = sum(1 for count in sources.values() if count > 0)
        
        agreement = source_count >= 2
        
        return {
            'keyword': keyword,
            'agreement': agreement,
            'source_count': source_count,
            'sources': sources,
            'confidence': 'HIGH' if source_count >= 3 else 'MEDIUM' if source_count == 2 else 'LOW'
        }
    
    def get_early_warnings(self, threshold: float = 50.0) -> List[Dict[str, Any]]:
        """
        Get early warning alerts for strong emerging trends.
        
        Args:
            threshold: Minimum strength score to trigger warning
            
        Returns:
            List of warning alerts
        """
        trends = self.detect_trends(window_hours=48)
        
        warnings = []
        for trend in trends:
            if trend['strength'] >= threshold:
                # Check velocity change
                velocity_high = abs(trend['velocity']) > 0.5
                
                # Check cross-source
                cross_source = self.check_cross_source_agreement(trend['keyword'], hours=24)
                
                if velocity_high and cross_source['agreement']:
                    warning = {
                        'keyword': trend['keyword'],
                        'alert_level': 'HIGH' if trend['strength'] > 70 else 'MEDIUM',
                        'strength': trend['strength'],
                        'velocity': trend['velocity'],
                        'sources': trend['sources'],
                        'confidence': cross_source['confidence'],
                        'recommendation': self._generate_recommendation(trend),
                        'timestamp': datetime.now().isoformat()
                    }
                    warnings.append(warning)
        
        logger.info(f"Generated {len(warnings)} early warnings")
        return warnings
    
    def _generate_recommendation(self, trend: Dict[str, Any]) -> str:
        """Generate actionable recommendation based on trend."""
        keyword = trend['keyword']
        velocity = trend['velocity']
        sentiment = trend['avg_sentiment']
        
        if velocity > 0.5 and sentiment > 0.3:
            return f"OPPORTUNITY: {keyword} showing strong positive momentum. Consider increasing inventory/marketing."
        elif velocity > 0.5 and sentiment < -0.3:
            return f"RISK: {keyword} showing negative sentiment surge. Review product quality/pricing."
        elif velocity < -0.5 and sentiment > 0:
            return f"CAUTION: {keyword} positive sentiment declining. Monitor closely for issues."
        elif abs(velocity) > 0.3:
            return f"MONITOR: {keyword} showing significant sentiment shift. Investigate cause."
        else:
            return f"WATCH: {keyword} trending. Continue monitoring."


if __name__ == "__main__":
    # Test trend detector
    import config
    
    print("=" * 70)
    print("TREND DETECTION TEST")
    print("=" * 70)
    
    db = DatabaseManager(config.DB_PATH)
    detector = TrendDetector(db)
    
    # Detect trends
    print("\nDetecting trends in last 48 hours...")
    trends = detector.detect_trends(window_hours=48)
    
    print(f"\nFound {len(trends)} trends:")
    print("=" * 70)
    
    for i, trend in enumerate(trends[:10], 1):
        print(f"\n{i}. {trend['keyword']}")
        print(f"   Strength: {trend['strength']:.1f}/100")
        print(f"   Velocity: {trend['velocity']:.3f}")
        print(f"   Growth Rate: {trend['growth_rate']:.1f}%")
        print(f"   Sources: {', '.join(trend['sources'])}")
        print(f"   Mentions: {trend['mention_count']}")
        print(f"   Avg Sentiment: {trend['avg_sentiment']:.3f}")
        print(f"   Signal: {trend['signal']}")
    
    # Get early warnings
    print("\n" + "=" * 70)
    print("EARLY WARNING SYSTEM")
    print("=" * 70)
    
    warnings = detector.get_early_warnings(threshold=40.0)
    
    if warnings:
        print(f"\n{len(warnings)} ALERTS:")
        for warning in warnings:
            print(f"\n[!] {warning['alert_level']} ALERT: {warning['keyword']}")
            print(f"  Strength: {warning['strength']:.1f}")
            print(f"  Confidence: {warning['confidence']}")
            print(f"  Recommendation: {warning['recommendation']}")
    else:
        print("\nNo high-priority alerts at this time.")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)

