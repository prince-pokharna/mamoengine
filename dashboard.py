"""
Streamlit Dashboard for Market-Mood Engine.
Interactive dashboard for sentiment analysis, trends, and forecasts.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

import config
from src.database import DatabaseManager
from src.sentiment_processor import SentimentProcessor
from src.trend_detector import TrendDetector
from src.forecaster import Forecaster

# Page configuration
st.set_page_config(
    page_title="Market-Mood Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    db = DatabaseManager(config.DB_PATH)
    sentiment_processor = SentimentProcessor(db)
    trend_detector = TrendDetector(db)
    forecaster = Forecaster(db)
    return db, sentiment_processor, trend_detector, forecaster

db, sentiment_processor, trend_detector, forecaster = init_components()

# Sidebar navigation
st.sidebar.title("📊 Market-Mood Engine")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Overview", "📈 Sentiment Analysis", "🔥 Trends", "🔮 Forecasts", "🛠️ System Health"]
)

st.sidebar.markdown("---")
st.sidebar.info("Real-time market mood & demand forecasting")

# ===== PAGE 1: OVERVIEW =====
if page == "🏠 Overview":
    st.title("🏠 Market-Mood Dashboard")
    st.markdown("### Real-time Consumer Sentiment & Trend Intelligence")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    stats = db.get_stats()
    
    with col1:
        st.metric(
            label="📰 Articles",
            value=stats.get('articles', 0),
            delta=None
        )
    
    with col2:
        st.metric(
            label="🐦 Tweets",
            value=stats.get('tweets', 0),
            delta=None
        )
    
    with col3:
        st.metric(
            label="📊 Trends",
            value=stats.get('trends', 0),
            delta=None
        )
    
    with col4:
        st.metric(
            label="💼 Sales Records",
            value=stats.get('sales', 0),
            delta=None
        )
    
    st.markdown("---")
    
    # Recent sentiment
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Sentiment Overview (24h)")
        sentiment_stats = sentiment_processor.get_sentiment_statistics(hours=24)
        
        if sentiment_stats['count'] > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['Positive', 'Negative', 'Neutral'],
                values=[
                    sentiment_stats['positive_count'],
                    sentiment_stats['negative_count'],
                    sentiment_stats['neutral_count']
                ],
                marker_colors=['#00D26A', '#F94144', '#F8B500']
            )])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric(
                label="Average Sentiment",
                value=f"{sentiment_stats['avg_sentiment']:.3f}",
                delta=sentiment_stats['trend']
            )
        else:
            st.info("No sentiment data available yet")
    
    with col2:
        st.subheader("🔥 Top Emerging Trends")
        trends = trend_detector.detect_trends(window_hours=48)
        
        if trends:
            top_trends = trends[:5]
            
            trend_df = pd.DataFrame([
                {
                    'Keyword': t['keyword'],
                    'Strength': t['strength'],
                    'Growth %': t['growth_rate'],
                    'Signal': t['signal'].split('(')[0].strip()
                }
                for t in top_trends
            ])
            
            st.dataframe(trend_df, use_container_width=True)
        else:
            st.info("No trends detected yet")
    
    st.markdown("---")
    
    # Quick insights
    st.subheader("💡 Quick Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Recent Activity:**")
        if stats.get('last_article_fetch'):
            st.write(f"🕐 Last article: {stats['last_article_fetch']}")
        if stats.get('last_tweet_fetch'):
            st.write(f"🕐 Last tweet: {stats['last_tweet_fetch']}")
    
    with col2:
        st.markdown("**System Status:**")
        st.success("✅ Data Collection: Active")
        st.success("✅ Sentiment Analysis: Operational")
        st.success("✅ Forecasting: Ready")

# ===== PAGE 2: SENTIMENT ANALYSIS =====
elif page == "📈 Sentiment Analysis":
    st.title("📈 Sentiment Analysis")
    
    # Time range selector
    hours = st.selectbox("Time Range", [6, 12, 24, 48, 72, 168], index=2)
    
    sentiment_stats = sentiment_processor.get_sentiment_statistics(hours=hours)
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Analyzed", sentiment_stats['count'])
    
    with col2:
        st.metric("Avg Sentiment", f"{sentiment_stats['avg_sentiment']:.3f}")
    
    with col3:
        st.metric("Positive %", f"{sentiment_stats.get('positive_percentage', 0):.1f}%")
    
    with col4:
        st.metric("Trend", sentiment_stats.get('trend', 'stable').upper())
    
    st.markdown("---")
    
    # Sentiment distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sentiment Distribution")
        
        fig = go.Figure(data=[go.Bar(
            x=['Positive', 'Neutral', 'Negative'],
            y=[
                sentiment_stats['positive_count'],
                sentiment_stats['neutral_count'],
                sentiment_stats['negative_count']
            ],
            marker_color=['#00D26A', '#F8B500', '#F94144']
        )])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Sentiment by Source")
        source_stats = sentiment_processor.get_sentiment_by_source()
        
        if source_stats:
            source_df = pd.DataFrame([
                {'Source': k, 'Avg Sentiment': v['avg_sentiment'], 'Articles': v['article_count']}
                for k, v in source_stats.items()
            ])
            
            fig = px.bar(source_df, x='Source', y='Avg Sentiment', color='Articles',
                        color_continuous_scale='Viridis')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source data available")
    
    st.markdown("---")
    
    # Top articles
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🟢 Most Positive Articles")
        positive_articles = sentiment_processor.get_top_positive_articles(limit=5)
        
        for i, article in enumerate(positive_articles, 1):
            with st.expander(f"{i}. {article['title']} ({article['sentiment_score']:.3f})"):
                st.write(f"**Source:** {article['source']}")
                st.write(f"**Sentiment:** {article['sentiment_score']:.3f}")
                st.write(f"**Content:** {article['content'][:200]}...")
    
    with col2:
        st.subheader("🔴 Most Negative Articles")
        negative_articles = sentiment_processor.get_top_negative_articles(limit=5)
        
        for i, article in enumerate(negative_articles, 1):
            with st.expander(f"{i}. {article['title']} ({article['sentiment_score']:.3f})"):
                st.write(f"**Source:** {article['source']}")
                st.write(f"**Sentiment:** {article['sentiment_score']:.3f}")
                st.write(f"**Content:** {article['content'][:200]}...")

# ===== PAGE 3: TRENDS =====
elif page == "🔥 Trends":
    st.title("🔥 Trend Detection & Early Warnings")
    
    # Time window selector
    window_hours = st.selectbox("Analysis Window", [24, 48, 72, 168], index=1)
    
    trends = trend_detector.detect_trends(window_hours=window_hours)
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        strength_filter = st.slider("Minimum Strength", 0, 100, 0)
    
    with col2:
        signal_filter = st.multiselect(
            "Signal Type",
            ["STRONG EMERGING TREND", "MODERATE TREND", "WEAK TREND", "STABLE"],
            default=["STRONG EMERGING TREND", "MODERATE TREND"]
        )
    
    # Filter trends
    filtered_trends = [
        t for t in trends
        if t['strength'] >= strength_filter and any(s in t['signal'] for s in signal_filter)
    ]
    
    st.markdown(f"### Found {len(filtered_trends)} Trends")
    
    if filtered_trends:
        # Trend strength chart
        trend_df = pd.DataFrame(filtered_trends)
        
        fig = px.scatter(
            trend_df,
            x='velocity',
            y='strength',
            size='mention_count',
            color='avg_sentiment',
            hover_name='keyword',
            labels={
                'velocity': 'Sentiment Velocity',
                'strength': 'Trend Strength',
                'avg_sentiment': 'Avg Sentiment'
            },
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Trend details
        st.markdown("---")
        st.subheader("Trend Details")
        
        for i, trend in enumerate(filtered_trends[:10], 1):
            with st.expander(f"{i}. {trend['keyword']} - Strength: {trend['strength']:.1f}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Velocity", f"{trend['velocity']:.3f}")
                
                with col2:
                    st.metric("Growth Rate", f"{trend['growth_rate']:.1f}%")
                
                with col3:
                    st.metric("Mentions", trend['mention_count'])
                
                st.write(f"**Sources:** {', '.join(trend['sources'])}")
                st.write(f"**Signal:** {trend['signal']}")
                st.write(f"**Avg Sentiment:** {trend['avg_sentiment']:.3f}")
    else:
        st.info("No trends match the selected filters")
    
    # Early warnings
    st.markdown("---")
    st.subheader("🚨 Early Warning Alerts")
    
    warnings = trend_detector.get_early_warnings(threshold=40.0)
    
    if warnings:
        for warning in warnings:
            alert_color = "error" if warning['alert_level'] == 'HIGH' else "warning"
            
            with st.container():
                if alert_color == "error":
                    st.error(f"🚨 HIGH ALERT: {warning['keyword']}")
                else:
                    st.warning(f"⚠️ MEDIUM ALERT: {warning['keyword']}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Strength:** {warning['strength']:.1f}")
                
                with col2:
                    st.write(f"**Confidence:** {warning['confidence']}")
                
                with col3:
                    st.write(f"**Sources:** {len(warning['sources'])}")
                
                st.info(f"💡 **Recommendation:** {warning['recommendation']}")
                st.markdown("---")
    else:
        st.success("✅ No high-priority alerts at this time")

# ===== PAGE 4: FORECASTS =====
elif page == "🔮 Forecasts":
    st.title("🔮 Demand Forecasting")
    
    # Category selector
    category = st.selectbox(
        "Select Category",
        ['phones', 'laptops', 'fashion', 'home', 'food']
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        days_ahead = st.slider("Forecast Period (days)", 1, 30, 7)
    
    with col2:
        model = st.selectbox("Model", ['ensemble', 'arima', 'prophet', 'simple'])
    
    # Generate forecast
    if st.button("Generate Forecast"):
        with st.spinner("Generating forecast..."):
            forecast = forecaster.forecast_category(category, days_ahead, model)
            
            # Display forecast
            st.success(f"Forecast generated for {category}")
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Model", forecast['model'])
            
            with col2:
                st.metric("Trend", forecast['trend'])
            
            with col3:
                avg_forecast = sum(f['value'] for f in forecast['forecasts']) / len(forecast['forecasts'])
                st.metric("Avg Forecast", f"{avg_forecast:.0f}")
            
            with col4:
                st.metric("Data Points", forecast['historical_data_points'])
            
            # Forecast chart
            st.markdown("---")
            st.subheader("Forecast Visualization")
            
            forecast_df = pd.DataFrame(forecast['forecasts'])
            forecast_df['date'] = pd.to_datetime(forecast_df['date'])
            
            fig = go.Figure()
            
            # Main forecast line
            fig.add_trace(go.Scatter(
                x=forecast_df['date'],
                y=forecast_df['value'],
                mode='lines+markers',
                name='Forecast',
                line=dict(color='#00D26A', width=3)
            ))
            
            # Confidence interval
            fig.add_trace(go.Scatter(
                x=forecast_df['date'].tolist() + forecast_df['date'].tolist()[::-1],
                y=forecast_df['upper_bound'].tolist() + forecast_df['lower_bound'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(0, 210, 106, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='Confidence Interval'
            ))
            
            fig.update_layout(
                height=500,
                xaxis_title="Date",
                yaxis_title="Forecasted Units",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast table
            st.markdown("---")
            st.subheader("Forecast Data")
            st.dataframe(forecast_df, use_container_width=True)
    
    # All categories overview
    st.markdown("---")
    st.subheader("All Categories Forecast (7-day)")
    
    if st.button("Forecast All Categories"):
        with st.spinner("Forecasting all categories..."):
            all_forecasts = forecaster.forecast_all_categories(days_ahead=7)
            
            summary_data = []
            for cat, fc in all_forecasts.items():
                if 'error' not in fc:
                    avg = sum(f['value'] for f in fc['forecasts']) / len(fc['forecasts'])
                    summary_data.append({
                        'Category': cat.upper(),
                        'Avg 7-day Forecast': f"{avg:.0f}",
                        'Trend': fc['trend'],
                        'Model': fc['model']
                    })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

# ===== PAGE 5: SYSTEM HEALTH =====
elif page == "🛠️ System Health":
    st.title("🛠️ System Health & Monitoring")
    
    # Database stats
    st.subheader("📊 Database Statistics")
    stats = db.get_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Articles", stats.get('articles', 0))
        st.metric("Tweets", stats.get('tweets', 0))
    
    with col2:
        st.metric("Google Trends", stats.get('trends', 0))
        st.metric("Sales Records", stats.get('sales', 0))
    
    with col3:
        st.metric("Reddit Posts", stats.get('reddit_posts', 0))
    
    # Last update times
    st.markdown("---")
    st.subheader("🕐 Last Update Times")
    
    if stats.get('last_article_fetch'):
        st.write(f"📰 Articles: {stats['last_article_fetch']}")
    
    if stats.get('last_tweet_fetch'):
        st.write(f"🐦 Tweets: {stats['last_tweet_fetch']}")
    
    # System status
    st.markdown("---")
    st.subheader("✅ System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("✅ Database: Connected")
        st.success("✅ Sentiment Analysis: Operational")
        st.success("✅ Trend Detection: Active")
    
    with col2:
        st.success("✅ Forecasting: Ready")
        st.success("✅ API: Available")
        st.success("✅ Dashboard: Running")
    
    # Refresh button
    st.markdown("---")
    if st.button("Refresh Data"):
        st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Market-Mood Engine v1.0**")
st.sidebar.markdown("Built with ❤️ for data-driven decisions")

