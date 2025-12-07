# Market-Mood Engine API Documentation

## Base URL
```
http://localhost:8000
```

## Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Authentication
Currently, the API does not require authentication (development version).

---

## Endpoints

### Health Check

#### `GET /health`
Check API health status and database connection.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-07T10:00:00",
  "database": {
    "connected": true,
    "articles": 100,
    "tweets": 250,
    "trends": 50
  }
}
```

---

### Sentiment Analysis

#### `GET /api/sentiment/analyze`
Analyze sentiment of provided text.

**Query Parameters:**
- `text` (required): Text to analyze

**Example:**
```bash
curl "http://localhost:8000/api/sentiment/analyze?text=iPhone%2015%20has%20amazing%20camera"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "text": "iPhone 15 has amazing camera",
    "overall_sentiment": 0.850,
    "confidence": 0.920,
    "emotion": {
      "positive": 0.900,
      "negative": 0.050,
      "neutral": 0.050
    },
    "trend_signal": "up"
  },
  "timestamp": "2025-12-07T10:00:00"
}
```

#### `GET /api/sentiment/statistics`
Get sentiment statistics for recent articles.

**Query Parameters:**
- `hours` (optional, default=24): Hours to look back

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 150,
    "avg_sentiment": 0.125,
    "positive_count": 80,
    "negative_count": 30,
    "neutral_count": 40,
    "positive_percentage": 53.3,
    "trend": "improving"
  }
}
```

#### `GET /api/sentiment/by-source`
Get average sentiment grouped by news source.

**Response:**
```json
{
  "success": true,
  "data": {
    "TechCrunch": {
      "avg_sentiment": 0.450,
      "article_count": 25
    },
    "Economic Times": {
      "avg_sentiment": 0.120,
      "article_count": 30
    }
  }
}
```

#### `GET /api/sentiment/top-positive`
Get most positive articles.

**Query Parameters:**
- `limit` (optional, default=5): Number of articles (1-50)

#### `GET /api/sentiment/top-negative`
Get most negative articles.

**Query Parameters:**
- `limit` (optional, default=5): Number of articles (1-50)

---

### Trend Detection

#### `GET /api/trends/detect`
Detect emerging market trends.

**Query Parameters:**
- `window_hours` (optional, default=48): Hours to analyze (12-168)

**Example:**
```bash
curl "http://localhost:8000/api/trends/detect?window_hours=48"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "keyword": "OnePlus",
      "strength": 75.5,
      "velocity": 0.850,
      "growth_rate": 250.0,
      "sources": ["news", "twitter", "google_trends"],
      "mention_count": 120,
      "avg_sentiment": 0.650,
      "signal": "STRONG EMERGING TREND (POSITIVE)",
      "detected_at": "2025-12-07T10:00:00"
    }
  ],
  "count": 10
}
```

#### `GET /api/trends/warnings`
Get early warning alerts for strong trends.

**Query Parameters:**
- `threshold` (optional, default=50): Minimum strength score (0-100)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "keyword": "OnePlus",
      "alert_level": "HIGH",
      "strength": 75.5,
      "velocity": 0.850,
      "sources": ["news", "twitter", "google_trends"],
      "confidence": "HIGH",
      "recommendation": "OPPORTUNITY: OnePlus showing strong positive momentum. Consider increasing inventory/marketing.",
      "timestamp": "2025-12-07T10:00:00"
    }
  ],
  "count": 3
}
```

---

### Forecasting

#### `GET /api/forecast/category/{category}`
Forecast demand for a specific category.

**Path Parameters:**
- `category` (required): One of [phones, laptops, fashion, home, food]

**Query Parameters:**
- `days_ahead` (optional, default=7): Days to forecast (1-30)
- `model` (optional, default=ensemble): Model [arima, prophet, ensemble, simple]

**Example:**
```bash
curl "http://localhost:8000/api/forecast/category/phones?days_ahead=7&model=ensemble"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "category": "phones",
    "model": "Ensemble",
    "trend": "UP",
    "historical_data_points": 14,
    "forecasts": [
      {
        "date": "2025-12-08T00:00:00",
        "value": 5200,
        "lower_bound": 4800,
        "upper_bound": 5600
      }
    ]
  }
}
```

#### `GET /api/forecast/all`
Forecast all product categories.

**Query Parameters:**
- `days_ahead` (optional, default=7): Days to forecast (1-30)

**Response:**
```json
{
  "success": true,
  "data": {
    "phones": { ... },
    "laptops": { ... },
    "fashion": { ... },
    "home": { ... },
    "food": { ... }
  }
}
```

---

### Data

#### `GET /api/data/stats`
Get database statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "articles": 150,
    "tweets": 300,
    "trends": 60,
    "sales": 45,
    "reddit_posts": 25,
    "last_article_fetch": "2025-12-07T10:00:00",
    "last_tweet_fetch": "2025-12-07T10:00:00"
  }
}
```

#### `GET /api/data/recent`
Get recent data from all sources.

**Query Parameters:**
- `hours` (optional, default=24): Hours to look back (1-168)

**Response:**
```json
{
  "success": true,
  "data": {
    "articles": [...],
    "tweets": [...],
    "trends": [...],
    "sales": [...],
    "reddit_posts": [...]
  },
  "counts": {
    "articles": 25,
    "tweets": 50,
    "trends": 10,
    "sales": 5,
    "reddit_posts": 8
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `500` - Internal Server Error

---

## Rate Limiting
Currently not implemented (development version).

In production:
- 100 requests per minute per IP
- 1000 requests per hour per IP

---

## Example Usage

### Python
```python
import requests

# Analyze sentiment
response = requests.get(
    "http://localhost:8000/api/sentiment/analyze",
    params={"text": "Amazing new phone launch!"}
)
result = response.json()
print(f"Sentiment: {result['data']['overall_sentiment']}")

# Get trends
response = requests.get("http://localhost:8000/api/trends/detect")
trends = response.json()['data']
for trend in trends[:5]:
    print(f"{trend['keyword']}: {trend['strength']}")
```

### JavaScript
```javascript
// Fetch forecast
fetch('http://localhost:8000/api/forecast/category/phones?days_ahead=7')
  .then(response => response.json())
  .then(data => {
    console.log('Forecast:', data.data.forecasts);
  });
```

### cURL
```bash
# Get sentiment statistics
curl "http://localhost:8000/api/sentiment/statistics?hours=24"

# Detect trends
curl "http://localhost:8000/api/trends/detect?window_hours=48"

# Forecast category
curl "http://localhost:8000/api/forecast/category/phones?days_ahead=7"
```

---

## Webhooks (Future Feature)
Webhook support for real-time alerts will be added in v2.0.

---

## Support
For issues or questions, please open a GitHub issue.

