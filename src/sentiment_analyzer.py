"""
Sentiment analysis engine for Market-Mood using DistilBERT.
Provides sentiment scoring, emotion classification, and entity extraction.
"""
import logging
from typing import List, Dict, Any, Optional
import re

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available, using mock sentiment analysis")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model cache to avoid reloading on every instantiation (as per developer guide)
_model_cache = {
    'sentiment_pipeline': None,
    'ner_pipeline': None
}


class SentimentAnalyzer:
    """
    Transformer-based sentiment analysis using DistilBERT.
    Provides overall sentiment, confidence, emotion breakdown, and entity sentiment.
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize sentiment analyzer with global model caching.
        
        Args:
            model_name: HuggingFace model identifier
        """
        global _model_cache
        
        self.model_name = model_name
        self.device = "cuda" if TRANSFORMERS_AVAILABLE and torch.cuda.is_available() else "cpu"
        
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use cached models if available (developer guide recommendation)
                if _model_cache['sentiment_pipeline'] is None:
                    logger.info(f"Loading model: {model_name} on {self.device}")
                    _model_cache['sentiment_pipeline'] = pipeline(
                        "sentiment-analysis",
                        model=model_name,
                        device=0 if self.device == "cuda" else -1
                    )
                    logger.info("Sentiment pipeline loaded and cached successfully")
                else:
                    logger.info("Using cached sentiment pipeline")
                
                self.sentiment_pipeline = _model_cache['sentiment_pipeline']
                
                # Load NER pipeline for entity extraction (cached)
                if _model_cache['ner_pipeline'] is None:
                    logger.info("Loading NER model")
                    _model_cache['ner_pipeline'] = pipeline(
                        "ner",
                        model="dslim/bert-base-NER",
                        device=0 if self.device == "cuda" else -1,
                        aggregation_strategy="simple"
                    )
                    logger.info("NER pipeline loaded and cached successfully")
                else:
                    logger.info("Using cached NER pipeline")
                
                self.ner_pipeline = _model_cache['ner_pipeline']
                
            except Exception as e:
                logger.error(f"Error loading transformers model: {e}")
                self.sentiment_pipeline = None
                self.ner_pipeline = None
        else:
            logger.warning("Transformers not available, using mock analysis")
            self.sentiment_pipeline = None
            self.ner_pipeline = None
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of single text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        # Handle empty or very short text
        if not text or len(text.strip()) < 5:
            return {
                "text": text,
                "overall_sentiment": 0.0,
                "confidence": 0.0,
                "emotion": {
                    "positive": 0.0,
                    "negative": 0.0,
                    "neutral": 1.0
                },
                "entities": [],
                "trend_signal": "stable",
                "error": "text_too_short"
            }
        
        # Truncate very long text
        text = text[:512]
        
        if self.sentiment_pipeline:
            try:
                return self._analyze_with_model(text)
            except Exception as e:
                logger.error(f"Error in model analysis: {e}")
                return self._mock_analysis(text)
        else:
            return self._mock_analysis(text)
    
    def _analyze_with_model(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using transformer model."""
        # Get sentiment prediction
        result = self.sentiment_pipeline(text)[0]
        
        # Convert to -1 to +1 scale
        label = result['label'].upper()
        score = result['score']
        
        if 'POSITIVE' in label or 'POS' in label:
            overall_sentiment = score
            positive_prob = score
            negative_prob = 1 - score
        else:  # NEGATIVE
            overall_sentiment = -score
            positive_prob = 1 - score
            negative_prob = score
        
        # Calculate neutral probability
        neutral_prob = 1.0 - abs(overall_sentiment)
        
        # Extract entities
        entities = self.extract_entities(text)
        
        # Determine trend signal
        trend_signal = self._calculate_trend_signal(overall_sentiment)
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "overall_sentiment": round(overall_sentiment, 3),
            "confidence": round(score, 3),
            "emotion": {
                "positive": round(positive_prob, 3),
                "negative": round(negative_prob, 3),
                "neutral": round(neutral_prob, 3)
            },
            "entities": entities[:5],  # Top 5 entities
            "trend_signal": trend_signal
        }
    
    def _mock_analysis(self, text: str) -> Dict[str, Any]:
        """
        Provide mock sentiment analysis using keyword-based approach.
        Used when transformers are not available.
        """
        text_lower = text.lower()
        
        # Simple keyword-based sentiment
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 
                         'fantastic', 'wonderful', 'awesome', 'perfect', 'happy',
                         'incredible', 'outstanding', 'brilliant', 'superb']
        
        negative_words = ['bad', 'terrible', 'horrible', 'awful', 'hate', 'worst',
                         'disappointing', 'poor', 'useless', 'boring', 'slow',
                         'expensive', 'overpriced', 'mediocre', 'disappointing']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate sentiment score
        total_words = len(text.split())
        if total_words == 0:
            sentiment_score = 0.0
        else:
            sentiment_score = (positive_count - negative_count) / max(total_words / 10, 1)
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Calculate confidence
        confidence = min(abs(sentiment_score) + 0.3, 0.95)
        
        # Calculate emotion probabilities
        if sentiment_score > 0:
            positive_prob = (sentiment_score + 1) / 2
            negative_prob = (1 - sentiment_score) / 2
        else:
            positive_prob = (sentiment_score + 1) / 2
            negative_prob = (1 - sentiment_score) / 2
        
        neutral_prob = 1.0 - positive_prob - negative_prob
        neutral_prob = max(0, neutral_prob)
        
        # Extract entities using simple pattern matching
        entities = self._extract_entities_simple(text)
        
        # Trend signal
        trend_signal = self._calculate_trend_signal(sentiment_score)
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "overall_sentiment": round(sentiment_score, 3),
            "confidence": round(confidence, 3),
            "emotion": {
                "positive": round(positive_prob, 3),
                "negative": round(negative_prob, 3),
                "neutral": round(neutral_prob, 3)
            },
            "entities": entities[:5],
            "trend_signal": trend_signal
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        if not texts:
            return []
        
        logger.info(f"Analyzing batch of {len(texts)} texts")
        results = []
        
        for i, text in enumerate(texts):
            if i % 20 == 0:
                logger.debug(f"Processing text {i+1}/{len(texts)}")
            
            result = self.analyze(text)
            results.append(result)
        
        logger.info(f"Batch analysis completed: {len(results)} results")
        return results
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text and their sentiment.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of entities with sentiment
        """
        # Always use simple extraction to avoid recursion
        return self._extract_entities_simple(text)
    
    def _extract_entities_simple(self, text: str) -> List[Dict[str, Any]]:
        """Simple keyword-based entity extraction."""
        # Common product/brand names in Indian market
        entities_keywords = [
            'iPhone', 'OnePlus', 'Samsung', 'Xiaomi', 'Realme', 'Oppo', 'Vivo',
            'Amazon', 'Flipkart', 'laptop', 'phone', 'smartphone', 'gadget',
            'camera', 'battery', 'display', 'screen'
        ]
        
        found_entities = []
        text_lower = text.lower()
        
        # Simple positive/negative words for context sentiment
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best']
        negative_words = ['bad', 'terrible', 'horrible', 'awful', 'hate', 'worst']
        
        for keyword in entities_keywords:
            if keyword.lower() in text_lower:
                # Get sentiment around this keyword
                idx = text_lower.find(keyword.lower())
                start = max(0, idx - 30)
                end = min(len(text), idx + len(keyword) + 30)
                context = text[start:end].lower()
                
                # Simple keyword-based sentiment for context only
                pos_count = sum(1 for word in positive_words if word in context)
                neg_count = sum(1 for word in negative_words if word in context)
                
                if pos_count > neg_count:
                    context_sentiment = 0.5
                elif neg_count > pos_count:
                    context_sentiment = -0.5
                else:
                    context_sentiment = 0.0
                
                found_entities.append({
                    "text": keyword,
                    "sentiment": context_sentiment,
                    "type": "product",
                    "confidence": 0.7
                })
        
        return found_entities
    
    def _calculate_trend_signal(self, sentiment_score: float) -> str:
        """
        Calculate trend signal based on sentiment.
        
        Args:
            sentiment_score: Sentiment score from -1 to 1
            
        Returns:
            Trend signal: 'up', 'down', or 'stable'
        """
        if sentiment_score > 0.3:
            return "up"
        elif sentiment_score < -0.3:
            return "down"
        else:
            return "stable"
    
    def update_trend_signal(self, historical_scores: List[float]) -> str:
        """
        Determine trend direction from historical sentiment scores.
        
        Args:
            historical_scores: List of sentiment scores over time
            
        Returns:
            Trend signal: 'up', 'down', or 'stable'
        """
        if not historical_scores or len(historical_scores) < 2:
            return "stable"
        
        # Calculate trend using simple linear regression
        n = len(historical_scores)
        x_mean = sum(range(n)) / n
        y_mean = sum(historical_scores) / n
        
        numerator = sum((i - x_mean) * (score - y_mean) 
                       for i, score in enumerate(historical_scores))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Determine trend based on slope
        if slope > 0.05:
            return "up"
        elif slope < -0.05:
            return "down"
        else:
            return "stable"
    
    def get_average_sentiment(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate average sentiment from multiple results.
        
        Args:
            results: List of sentiment analysis results
            
        Returns:
            Dictionary with aggregated statistics
        """
        if not results:
            return {
                "average_sentiment": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "total_count": 0
            }
        
        sentiments = [r['overall_sentiment'] for r in results]
        
        positive_count = sum(1 for s in sentiments if s > 0.3)
        negative_count = sum(1 for s in sentiments if s < -0.3)
        neutral_count = len(sentiments) - positive_count - negative_count
        
        return {
            "average_sentiment": round(sum(sentiments) / len(sentiments), 3),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "total_count": len(results),
            "positive_percentage": round(positive_count / len(results) * 100, 1),
            "negative_percentage": round(negative_count / len(results) * 100, 1),
            "neutral_percentage": round(neutral_count / len(results) * 100, 1)
        }


if __name__ == "__main__":
    # Test the sentiment analyzer
    analyzer = SentimentAnalyzer()
    
    test_texts = [
        "iPhone 15 Pro has an amazing camera!",
        "Terrible battery life on new OnePlus",
        "Amazon sale starting tomorrow",
        "This product is absolutely terrible and horrible",
        "The new phone is okay, nothing special",
        "Loving the new gadgets coming out this month"
    ]
    
    print("\n" + "=" * 60)
    print("SENTIMENT ANALYSIS TEST")
    print("=" * 60)
    
    for text in test_texts:
        result = analyzer.analyze(text)
        sentiment = result['overall_sentiment']
        confidence = result['confidence']
        
        # Format sentiment display
        if sentiment > 0:
            sentiment_label = "POSITIVE"
        elif sentiment < 0:
            sentiment_label = "NEGATIVE"
        else:
            sentiment_label = "NEUTRAL"
        
        print(f"\nText: {text}")
        print(f"Sentiment: {sentiment_label} ({sentiment:.3f})")
        print(f"Confidence: {confidence:.3f}")
        print(f"Trend: {result['trend_signal']}")
    
    # Test batch analysis
    print("\n" + "=" * 60)
    print("BATCH ANALYSIS")
    print("=" * 60)
    results = analyzer.analyze_batch(test_texts)
    stats = analyzer.get_average_sentiment(results)
    print(f"\nAverage sentiment: {stats['average_sentiment']}")
    print(f"Positive: {stats['positive_count']} ({stats['positive_percentage']}%)")
    print(f"Negative: {stats['negative_count']} ({stats['negative_percentage']}%)")
    print(f"Neutral: {stats['neutral_count']} ({stats['neutral_percentage']}%)")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

