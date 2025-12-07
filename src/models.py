"""
Data models for Market-Mood Engine using Pydantic.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class Article(BaseModel):
    """News article data model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    source: str
    title: str
    content: str
    published_date: datetime
    fetched_date: datetime = Field(default_factory=datetime.now)
    url: str
    sentiment_score: Optional[float] = None
    sentiment_emotion: Optional[str] = None
    processed_at: Optional[datetime] = None


class Tweet(BaseModel):
    """Twitter/social media post data model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    text: str
    author: str
    created_date: datetime
    likes: int = 0
    retweets: int = 0
    source_name: str = "twitter"
    fetched_date: datetime = Field(default_factory=datetime.now)


class GoogleTrend(BaseModel):
    """Google Trends search volume data model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    keyword: str
    search_volume: int
    date: datetime
    category: Optional[str] = None
    fetched_date: datetime = Field(default_factory=datetime.now)


class EcommerceSale(BaseModel):
    """E-commerce sales data model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    category: str
    sales_count: int
    date: datetime
    region: str = "India"
    fetched_date: datetime = Field(default_factory=datetime.now)


class RedditPost(BaseModel):
    """Reddit post data model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    title: str
    text: str
    subreddit: str
    score: int
    created_date: datetime
    fetched_date: datetime = Field(default_factory=datetime.now)


class ValidationReport(BaseModel):
    """Data validation report model."""
    total_records: int
    valid_records: int
    invalid_records: int
    validation_date: datetime = Field(default_factory=datetime.now)
    reasons: Dict[str, int] = Field(default_factory=dict)
