"""
Unit tests for sentiment analysis module.
"""
import pytest
from src.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer:
    """Test cases for SentimentAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create SentimentAnalyzer instance for testing."""
        return SentimentAnalyzer()
    
    def test_positive_sentiment(self, analyzer):
        """Test positive sentiment detection."""
        text = "This product is absolutely amazing and wonderful!"
        result = analyzer.analyze(text)
        
        assert result['overall_sentiment'] > 0, "Should detect positive sentiment"
        assert result['confidence'] > 0, "Should have confidence score"
        assert result['trend_signal'] in ['up', 'stable'], "Should indicate upward trend"
    
    def test_negative_sentiment(self, analyzer):
        """Test negative sentiment detection."""
        text = "This product is terrible and awful. Waste of money."
        result = analyzer.analyze(text)
        
        assert result['overall_sentiment'] < 0, "Should detect negative sentiment"
        assert result['trend_signal'] in ['down', 'stable'], "Should indicate downward trend"
    
    def test_neutral_sentiment(self, analyzer):
        """Test neutral sentiment detection."""
        text = "The product was delivered on time."
        result = analyzer.analyze(text)
        
        assert result['overall_sentiment'] is not None, "Should return sentiment score"
        assert -1 <= result['overall_sentiment'] <= 1, "Sentiment should be in valid range"
    
    def test_short_text(self, analyzer):
        """Test handling of short text."""
        text = "OK"
        result = analyzer.analyze(text)
        
        assert 'error' in result or result['overall_sentiment'] is not None
    
    def test_empty_text(self, analyzer):
        """Test handling of empty text."""
        text = ""
        result = analyzer.analyze(text)
        
        assert 'error' in result, "Should return error for empty text"
    
    def test_batch_analysis(self, analyzer):
        """Test batch sentiment analysis."""
        texts = [
            "Great product, highly recommend!",
            "Poor quality, very disappointed.",
            "Average performance, nothing special."
        ]
        
        results = analyzer.analyze_batch(texts)
        
        assert len(results) == 3, "Should return result for each text"
        assert all('overall_sentiment' in r for r in results), "All should have sentiment"
    
    def test_sentiment_range(self, analyzer):
        """Test sentiment scores are in valid range."""
        texts = [
            "Excellent amazing wonderful fantastic great",
            "Terrible horrible awful bad poor",
            "Okay fine normal average regular"
        ]
        
        for text in texts:
            result = analyzer.analyze(text)
            sentiment = result['overall_sentiment']
            assert -1 <= sentiment <= 1, f"Sentiment {sentiment} out of range [-1, 1]"
    
    def test_confidence_range(self, analyzer):
        """Test confidence scores are in valid range."""
        text = "This is a test sentence with some sentiment."
        result = analyzer.analyze(text)
        
        confidence = result['confidence']
        assert 0 <= confidence <= 1, f"Confidence {confidence} out of range [0, 1]"
    
    def test_emotion_breakdown(self, analyzer):
        """Test emotion breakdown sums to approximately 1."""
        text = "I love this new phone!"
        result = analyzer.analyze(text)
        
        emotions = result['emotion']
        total = emotions['positive'] + emotions['negative'] + emotions['neutral']
        
        assert 0.9 <= total <= 1.1, f"Emotions should sum to ~1, got {total}"
    
    def test_get_average_sentiment(self, analyzer):
        """Test average sentiment calculation."""
        results = [
            {'overall_sentiment': 0.5},
            {'overall_sentiment': -0.3},
            {'overall_sentiment': 0.2}
        ]
        
        avg_stats = analyzer.get_average_sentiment(results)
        
        assert 'average_sentiment' in avg_stats
        assert 'positive_count' in avg_stats
        assert 'total_count' in avg_stats
        assert avg_stats['total_count'] == 3


class TestTrendSignal:
    """Test trend signal calculation."""
    
    @pytest.fixture
    def analyzer(self):
        return SentimentAnalyzer()
    
    def test_update_trend_signal_upward(self, analyzer):
        """Test upward trend detection."""
        scores = [-0.5, -0.2, 0.1, 0.3, 0.6]
        signal = analyzer.update_trend_signal(scores)
        
        assert signal == 'up', "Should detect upward trend"
    
    def test_update_trend_signal_downward(self, analyzer):
        """Test downward trend detection."""
        scores = [0.6, 0.3, 0.1, -0.2, -0.5]
        signal = analyzer.update_trend_signal(scores)
        
        assert signal == 'down', "Should detect downward trend"
    
    def test_update_trend_signal_stable(self, analyzer):
        """Test stable trend detection."""
        scores = [0.2, 0.25, 0.22, 0.23, 0.24]
        signal = analyzer.update_trend_signal(scores)
        
        assert signal == 'stable', "Should detect stable trend"
    
    def test_insufficient_data(self, analyzer):
        """Test handling of insufficient historical data."""
        scores = [0.5]
        signal = analyzer.update_trend_signal(scores)
        
        assert signal == 'stable', "Should return stable for insufficient data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

