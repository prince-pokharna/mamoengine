# 🚀 Market-Mood Engine

Predict what consumers will want BEFORE trends become mainstream using AI sentiment analysis and trend forecasting.

## 📋 Problem

Businesses spend millions predicting consumer demand with outdated methods. Market-Mood detects emerging trends in real-time by analyzing news, social media, and e-commerce patterns across Indian markets.

## 💡 Solution

A real-time AI system that:
- Analyzes sentiment across 5+ data sources
- Detects emerging trends before competitors
- Forecasts demand 1-4 weeks ahead
- Provides actionable intelligence via API + dashboard

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│         DATA SOURCES (Real + Mock)                  │
│  News API │ Twitter │ Google Trends │ Ecommerce    │
└────────────────────┬────────────────────────────────┘
                     ↓
        ┌────────────────────────────┐
        │ Data Ingestion & Validation│
        │      (Hourly batch)        │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │     SQLite Database        │
        │  (articles, tweets, etc.)  │
        └────────────┬───────────────┘
                     ↓
        ┌───────────────────────────────────┐
        │  NLP & Sentiment Analysis (BERT)  │
        └──────────────┬────────────────────┘
                       ↓
        ┌──────────────────────────────────┐
        │ Trend Detection & Forecasting    │
        │    (ARIMA, Prophet, LSTM)        │
        └──────────────┬───────────────────┘
                       ↓
        ┌──────────────────────────────────┐
        │  REST API + Streamlit Dashboard  │
        └──────────────────────────────────┘
```

## ⚡ Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to repository
cd market-mood-engine

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Configure API Keys (Optional)

Get API keys from:
- **News API**: https://newsapi.org/ (free tier)
- **Twitter API**: https://developer.twitter.com/ (free tier)
- **Google Trends**: No API key needed (uses pytrends)

Add to `.env` file:
```
NEWS_API_KEY=your_newsapi_key
TWITTER_API_KEY=your_twitter_key
TWITTER_API_SECRET=your_twitter_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_secret
```

> **Note**: The system works with mock data if API keys are not configured, perfect for testing!

### 3. Initialize Database

```bash
python -c "from src.database import DatabaseManager; import config; db = DatabaseManager(config.DB_PATH); db.create_tables(); print('Database initialized!')"
```

### 4. Run Data Collection

```bash
# Test the pipeline
python test_pipeline.py

# Or run data ingestion directly
python src/data_ingestion.py
```

### 5. Schedule Hourly Collection (Optional)

**Windows (Task Scheduler):**
```powershell
# Create a task to run hourly
schtasks /create /tn "MarketMoodCollection" /tr "python D:\mamoengine\src\data_ingestion.py" /sc hourly
```

**Linux/Mac (Cron):**
```bash
# Add to crontab
0 * * * * cd /path/to/market-mood-engine && python src/data_ingestion.py
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Data Sources** | NewsAPI, Twitter API, Google Trends, SQLite |
| **NLP** | Hugging Face Transformers (DistilBERT) |
| **Machine Learning** | scikit-learn, PyTorch, Statsmodels |
| **Time Series** | ARIMA, Prophet, LSTM |
| **API** | FastAPI + Uvicorn |
| **Dashboard** | Streamlit |
| **Deployment** | Docker |

## 📊 Key Features

### ✅ Day 1-2: Data Pipeline (COMPLETED)
- ✅ Multi-source data collection (News, Twitter, Google Trends)
- ✅ SQLite database with optimized schema
- ✅ Mock data generators for testing
- ✅ Error handling & retry logic
- ✅ Duplicate detection
- ✅ Production-ready logging

### ⏳ Day 3: Sentiment Analysis (UPCOMING)
- Transformer-based sentiment analysis (DistilBERT)
- Entity extraction & aspect-based sentiment
- Emotion classification
- Confidence scoring

### ⏳ Day 4: Trend Detection (UPCOMING)
- Sentiment velocity tracking
- Cross-source trend validation
- Early warning system
- Trend strength scoring

### ⏳ Day 5: Forecasting (UPCOMING)
- Multi-model ensemble (ARIMA + Prophet + LSTM)
- 1-4 week demand forecasting
- Concept drift detection
- Confidence intervals

### ⏳ Day 6: API + Dashboard (UPCOMING)
- REST API endpoints
- Interactive Streamlit dashboard
- Real-time updates
- Data visualization

### ⏳ Day 7: Testing + Polish (UPCOMING)
- Unit & integration tests
- Docker containerization
- Documentation
- Production deployment guide

## 📁 Project Structure

```
market-mood-engine/
├── data/
│   ├── raw/                 # Raw data files (gitignored)
│   ├── processed/           # Processed data (gitignored)
│   └── market_mood.db       # SQLite database (gitignored)
├── src/
│   ├── __init__.py          # Package initialization
│   ├── database.py          # Database manager
│   ├── data_ingestion.py    # Data collection pipeline
│   ├── models.py            # Pydantic data models
│   ├── sentiment_analyzer.py    # (Day 3)
│   ├── trend_detector.py        # (Day 4)
│   └── forecaster.py            # (Day 5)
├── notebooks/               # Jupyter notebooks for analysis
├── tests/                   # Unit tests
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── test_pipeline.py        # Pipeline testing script
├── .env.example            # Environment variables template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🎯 Target Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Sentiment Accuracy | 85%+ | ⏳ Day 3 |
| Trend Detection Precision | 80%+ | ⏳ Day 4 |
| Forecast MAPE | <15% | ⏳ Day 5 |
| API Latency (p95) | <200ms | ⏳ Day 6 |
| Test Coverage | 80%+ | ⏳ Day 7 |

## 📈 Current Status

**🚧 In Progress - 7 Day Sprint**

| Day | Task | Status |
|-----|------|--------|
| **Day 1-2** | Data Pipeline Foundation | ✅ **COMPLETED** |
| **Day 3** | Sentiment Analysis | ⏳ Pending |
| **Day 4** | Trend Detection | ⏳ Pending |
| **Day 5** | Forecasting Models | ⏳ Pending |
| **Day 6** | API + Dashboard | ⏳ Pending |
| **Day 7** | Testing + Polish | ⏳ Pending |

### Day 1-2 Achievements ✅
- ✅ Complete data ingestion pipeline with 5 collectors
- ✅ SQLite database with optimized schema & indexes
- ✅ Production-grade error handling & retry logic
- ✅ Mock data generators for testing without API keys
- ✅ Comprehensive logging system
- ✅ Data deduplication by URL/text/date
- ✅ Tested and verified - collecting 30+ data points per run

## 🧪 Testing

Run the test suite:
```bash
python test_pipeline.py
```

Expected output:
```
[SUCCESS] ALL TESTS PASSED - Day 1 Complete!
Articles collected: 5
Tweets collected: 10
Trends collected: 5
Sales collected: 5
Reddit posts collected: 5
```

## 🔍 Example Usage

```python
from src.database import DatabaseManager
from src.data_ingestion import DataPipeline
import config

# Initialize
db = DatabaseManager(config.DB_PATH)
db.create_tables()

# Collect data
pipeline = DataPipeline(db)
stats = pipeline.run_hourly()

# Query recent data
recent_data = db.get_recent_data(hours=24)
print(f"Articles: {len(recent_data['articles'])}")
print(f"Tweets: {len(recent_data['tweets'])}")

# Get statistics
db_stats = db.get_stats()
print(f"Total records: {db_stats}")
```

## 🤝 Contributing

This is a portfolio/learning project following a structured 7-day sprint. Contributions and feedback are welcome!

## 📝 License

MIT License - Feel free to use this for learning and portfolio purposes.

## 🎓 Learning Outcomes

This project demonstrates:
- Production-grade data pipeline design
- Multi-source data integration
- NLP & sentiment analysis
- Time series forecasting
- REST API development
- Dashboard creation
- Docker containerization
- Testing & documentation best practices

---

**Built with ❤️ as part of a 7-day intensive learning sprint**

Last Updated: Day 2 - December 7, 2025

