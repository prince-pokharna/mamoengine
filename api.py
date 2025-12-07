"""
FastAPI REST API for Market-Mood Engine.
Provides endpoints for sentiment, trends, and forecasts.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime
import uvicorn

import config
from src.database import DatabaseManager
from src.sentiment_analyzer import SentimentAnalyzer
from src.sentiment_processor import SentimentProcessor
from src.trend_detector import TrendDetector
from src.forecaster import Forecaster

# Initialize FastAPI app
app = FastAPI(
    title="Market-Mood API",
    description="Real-time sentiment analysis, trend detection, and demand forecasting API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = DatabaseManager(config.DB_PATH)
sentiment_analyzer = SentimentAnalyzer()
sentiment_processor = SentimentProcessor(db, sentiment_analyzer)
trend_detector = TrendDetector(db)
forecaster = Forecaster(db)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Market-Mood Engine API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "sentiment": "/api/sentiment/*",
            "trends": "/api/trends/*",
            "forecast": "/api/forecast/*",
            "data": "/api/data/*"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        stats = db.get_stats()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connected": True,
                "articles": stats.get('articles', 0),
                "tweets": stats.get('tweets', 0),
                "trends": stats.get('trends', 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/api/sentiment/analyze")
async def analyze_sentiment(text: str = Query(..., description="Text to analyze")):
    """
    Analyze sentiment of provided text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Sentiment analysis results
    """
    if not text or len(text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Text too short (minimum 5 characters)")
    
    try:
        result = sentiment_analyzer.analyze(text)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/sentiment/statistics")
async def get_sentiment_statistics(hours: int = Query(24, description="Hours to look back")):
    """
    Get sentiment statistics for recent articles.
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        Sentiment statistics
    """
    try:
        stats = sentiment_processor.get_sentiment_statistics(hours=hours)
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.get("/api/sentiment/by-source")
async def get_sentiment_by_source():
    """Get average sentiment grouped by source."""
    try:
        stats = sentiment_processor.get_sentiment_by_source()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sentiment by source: {str(e)}")


@app.get("/api/sentiment/top-positive")
async def get_top_positive(limit: int = Query(5, description="Number of articles", ge=1, le=50)):
    """Get top positive articles."""
    try:
        articles = sentiment_processor.get_top_positive_articles(limit=limit)
        return {
            "success": True,
            "data": articles,
            "count": len(articles),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")


@app.get("/api/sentiment/top-negative")
async def get_top_negative(limit: int = Query(5, description="Number of articles", ge=1, le=50)):
    """Get top negative articles."""
    try:
        articles = sentiment_processor.get_top_negative_articles(limit=limit)
        return {
            "success": True,
            "data": articles,
            "count": len(articles),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")


@app.get("/api/trends/detect")
async def detect_trends(window_hours: int = Query(48, description="Hours to analyze", ge=12, le=168)):
    """
    Detect emerging trends.
    
    Args:
        window_hours: Time window to analyze in hours
        
    Returns:
        List of detected trends
    """
    try:
        trends = trend_detector.detect_trends(window_hours=window_hours)
        return {
            "success": True,
            "data": trends,
            "count": len(trends),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend detection failed: {str(e)}")


@app.get("/api/trends/warnings")
async def get_early_warnings(threshold: float = Query(50.0, description="Strength threshold", ge=0, le=100)):
    """
    Get early warning alerts for strong trends.
    
    Args:
        threshold: Minimum strength score to trigger warning
        
    Returns:
        List of warning alerts
    """
    try:
        warnings = trend_detector.get_early_warnings(threshold=threshold)
        return {
            "success": True,
            "data": warnings,
            "count": len(warnings),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get warnings: {str(e)}")


@app.get("/api/forecast/category/{category}")
async def forecast_category(
    category: str,
    days_ahead: int = Query(7, description="Days to forecast", ge=1, le=30),
    model: str = Query('ensemble', description="Model to use (arima/prophet/ensemble/simple)")
):
    """
    Forecast demand for a category.
    
    Args:
        category: Product category
        days_ahead: Days to forecast ahead
        model: Model to use for forecasting
        
    Returns:
        Forecast results
    """
    valid_categories = ['phones', 'laptops', 'fashion', 'home', 'food']
    if category not in valid_categories:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )
    
    valid_models = ['arima', 'prophet', 'ensemble', 'simple']
    if model not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Must be one of: {', '.join(valid_models)}"
        )
    
    try:
        forecast = forecaster.forecast_category(category, days_ahead, model)
        return {
            "success": True,
            "data": forecast,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")


@app.get("/api/forecast/all")
async def forecast_all_categories(days_ahead: int = Query(7, description="Days to forecast", ge=1, le=30)):
    """
    Forecast all product categories.
    
    Args:
        days_ahead: Days to forecast ahead
        
    Returns:
        Forecasts for all categories
    """
    try:
        forecasts = forecaster.forecast_all_categories(days_ahead=days_ahead)
        return {
            "success": True,
            "data": forecasts,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")


@app.get("/api/data/stats")
async def get_database_stats():
    """Get database statistics."""
    try:
        stats = db.get_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/api/data/recent")
async def get_recent_data(hours: int = Query(24, description="Hours to look back", ge=1, le=168)):
    """
    Get recent data from all sources.
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        Recent data from all sources
    """
    try:
        data = db.get_recent_data(hours=hours)
        
        # Convert to JSON-serializable format
        for key in data:
            for item in data[key]:
                for k, v in item.items():
                    if isinstance(v, datetime):
                        item[k] = v.isoformat()
        
        return {
            "success": True,
            "data": data,
            "counts": {k: len(v) for k, v in data.items()},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent data: {str(e)}")


if __name__ == "__main__":
    print("=" * 70)
    print("MARKET-MOOD ENGINE API")
    print("=" * 70)
    print("\nStarting API server...")
    print("API Documentation: http://localhost:8000/docs")
    print("API Base URL: http://localhost:8000")
    print("\nPress Ctrl+C to stop")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

