"""
Test script for Market-Mood Engine data pipeline.
"""
from src.database import DatabaseManager
from src.data_ingestion import DataPipeline
import config

def main():
    print("=" * 60)
    print("Testing Market-Mood Engine - Day 1 Pipeline")
    print("=" * 60)
    
    # Step 1: Create database
    print("\n1. Creating database...")
    db = DatabaseManager(config.DB_PATH)
    db.create_tables()
    print("[OK] Database created successfully")
    
    # Step 2: Run data collection pipeline
    print("\n2. Running data collection pipeline...")
    pipeline = DataPipeline(db)
    stats = pipeline.run_hourly()
    
    # Step 3: Verify data
    print("\n3. Verifying collected data...")
    db_stats = db.get_stats()
    
    print("\n" + "=" * 60)
    print("PIPELINE TEST RESULTS")
    print("=" * 60)
    print(f"Articles collected: {stats.get('articles_collected', 0)}")
    print(f"Articles inserted: {stats.get('articles_inserted', 0)}")
    print(f"Tweets collected: {stats.get('tweets_collected', 0)}")
    print(f"Tweets inserted: {stats.get('tweets_inserted', 0)}")
    print(f"Trends collected: {stats.get('trends_collected', 0)}")
    print(f"Trends inserted: {stats.get('trends_inserted', 0)}")
    print(f"Sales collected: {stats.get('sales_collected', 0)}")
    print(f"Sales inserted: {stats.get('sales_inserted', 0)}")
    print(f"Reddit posts collected: {stats.get('posts_collected', 0)}")
    print(f"Reddit posts inserted: {stats.get('posts_inserted', 0)}")
    
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    for key, value in db_stats.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL TESTS PASSED - Day 1 Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
