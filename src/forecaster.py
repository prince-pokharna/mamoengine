"""
Forecasting engine for Market-Mood.
Provides demand forecasting using ARIMA, Prophet, and ensemble methods.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

import pandas as pd
import numpy as np

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tools.sm_exceptions import ConvergenceWarning
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    logging.warning("statsmodels not available, ARIMA forecasting disabled")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not available, Prophet forecasting disabled")

from src.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Forecaster:
    """
    Multi-model demand forecasting engine.
    Supports ARIMA, Prophet, and ensemble forecasting.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize forecaster.
        
        Args:
            db: DatabaseManager instance
        """
        self.db = db
        self.models = {}
        self.forecast_cache = {}
        logger.info("Forecaster initialized")
    
    def prepare_time_series_data(self, category: str, days: int = 14) -> pd.DataFrame:
        """
        Prepare time series data for forecasting.
        
        Args:
            category: Product category to forecast
            days: Number of historical days to include
            
        Returns:
            DataFrame with time series data
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.db.get_connection() as conn:
            query = """
                SELECT date, sales_count
                FROM ecommerce_sales
                WHERE category = ?
                  AND date >= ?
                ORDER BY date ASC
            """
            
            df = pd.read_sql_query(query, conn, params=(category, cutoff_date))
        
        if df.empty:
            logger.warning(f"No data found for category: {category}")
            return pd.DataFrame()
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Aggregate by day (sum sales for same day)
        df = df.groupby('date').agg({'sales_count': 'sum'}).reset_index()
        
        # Fill missing dates
        date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
        df = df.set_index('date').reindex(date_range).fillna(method='ffill').reset_index()
        df.columns = ['date', 'sales_count']
        
        logger.info(f"Prepared {len(df)} data points for {category}")
        return df
    
    def forecast_arima(self, data: pd.DataFrame, periods: int = 7) -> Dict[str, Any]:
        """
        Forecast using ARIMA model.
        
        Args:
            data: Time series data (date, value columns)
            periods: Number of periods to forecast
            
        Returns:
            Dictionary with forecast results
        """
        if not ARIMA_AVAILABLE or data.empty or len(data) < 7:
            logger.warning("ARIMA not available or insufficient data")
            return self._simple_forecast(data, periods)
        
        try:
            # Prepare data
            ts_data = data['sales_count'].values
            
            # Fit ARIMA model (p=1, d=1, q=1 - simple model)
            model = ARIMA(ts_data, order=(1, 1, 1))
            fitted_model = model.fit()
            
            # Forecast
            forecast = fitted_model.forecast(steps=periods)
            
            # Get confidence intervals
            forecast_df = fitted_model.get_forecast(steps=periods)
            conf_int = forecast_df.conf_int()
            
            # Prepare results
            last_date = data['date'].max()
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(periods)]
            
            results = {
                'model': 'ARIMA',
                'forecasts': [
                    {
                        'date': date.isoformat(),
                        'value': max(0, float(val)),
                        'lower_bound': max(0, float(conf_int.iloc[i, 0])),
                        'upper_bound': float(conf_int.iloc[i, 1])
                    }
                    for i, (date, val) in enumerate(zip(forecast_dates, forecast))
                ],
                'model_params': {
                    'order': '(1,1,1)',
                    'aic': float(fitted_model.aic),
                    'bic': float(fitted_model.bic)
                }
            }
            
            logger.info(f"ARIMA forecast completed: {periods} periods")
            return results
            
        except Exception as e:
            logger.error(f"ARIMA forecasting error: {e}")
            return self._simple_forecast(data, periods)
    
    def forecast_prophet(self, data: pd.DataFrame, periods: int = 7) -> Dict[str, Any]:
        """
        Forecast using Prophet model.
        
        Args:
            data: Time series data
            periods: Number of periods to forecast
            
        Returns:
            Dictionary with forecast results
        """
        if not PROPHET_AVAILABLE or data.empty or len(data) < 7:
            logger.warning("Prophet not available or insufficient data")
            return self._simple_forecast(data, periods)
        
        try:
            # Prepare data for Prophet (requires 'ds' and 'y' columns)
            prophet_df = pd.DataFrame({
                'ds': data['date'],
                'y': data['sales_count']
            })
            
            # Initialize and fit model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False,
                interval_width=0.95
            )
            
            # Suppress Prophet logging
            import logging as base_logging
            base_logging.getLogger('prophet').setLevel(base_logging.WARNING)
            
            model.fit(prophet_df)
            
            # Make future dataframe
            future = model.make_future_dataframe(periods=periods)
            
            # Forecast
            forecast = model.predict(future)
            
            # Extract last 'periods' predictions
            forecast_results = forecast.tail(periods)
            
            results = {
                'model': 'Prophet',
                'forecasts': [
                    {
                        'date': row['ds'].isoformat(),
                        'value': max(0, float(row['yhat'])),
                        'lower_bound': max(0, float(row['yhat_lower'])),
                        'upper_bound': float(row['yhat_upper'])
                    }
                    for _, row in forecast_results.iterrows()
                ],
                'model_params': {
                    'seasonality': 'daily_weekly',
                    'interval_width': 0.95
                }
            }
            
            logger.info(f"Prophet forecast completed: {periods} periods")
            return results
            
        except Exception as e:
            logger.error(f"Prophet forecasting error: {e}")
            return self._simple_forecast(data, periods)
    
    def forecast_ensemble(self, data: pd.DataFrame, periods: int = 7) -> Dict[str, Any]:
        """
        Ensemble forecast combining ARIMA and Prophet.
        
        Args:
            data: Time series data
            periods: Number of periods to forecast
            
        Returns:
            Dictionary with ensemble forecast results
        """
        if data.empty or len(data) < 7:
            return self._simple_forecast(data, periods)
        
        # Get individual forecasts
        arima_forecast = self.forecast_arima(data, periods)
        prophet_forecast = self.forecast_prophet(data, periods)
        
        # Weights (can be adjusted based on historical accuracy)
        arima_weight = 0.4
        prophet_weight = 0.6
        
        # Combine forecasts
        ensemble_forecasts = []
        
        for i in range(periods):
            arima_val = arima_forecast['forecasts'][i]['value']
            prophet_val = prophet_forecast['forecasts'][i]['value']
            
            ensemble_value = (arima_weight * arima_val) + (prophet_weight * prophet_val)
            
            # Conservative confidence bounds (wider of the two)
            arima_lower = arima_forecast['forecasts'][i]['lower_bound']
            prophet_lower = prophet_forecast['forecasts'][i]['lower_bound']
            lower_bound = min(arima_lower, prophet_lower)
            
            arima_upper = arima_forecast['forecasts'][i]['upper_bound']
            prophet_upper = prophet_forecast['forecasts'][i]['upper_bound']
            upper_bound = max(arima_upper, prophet_upper)
            
            ensemble_forecasts.append({
                'date': arima_forecast['forecasts'][i]['date'],
                'value': round(ensemble_value, 0),
                'lower_bound': round(max(0, lower_bound), 0),
                'upper_bound': round(upper_bound, 0),
                'arima_value': round(arima_val, 0),
                'prophet_value': round(prophet_val, 0)
            })
        
        results = {
            'model': 'Ensemble',
            'forecasts': ensemble_forecasts,
            'model_params': {
                'arima_weight': arima_weight,
                'prophet_weight': prophet_weight,
                'models': ['ARIMA(1,1,1)', 'Prophet']
            }
        }
        
        logger.info(f"Ensemble forecast completed: {periods} periods")
        return results
    
    def _simple_forecast(self, data: pd.DataFrame, periods: int) -> Dict[str, Any]:
        """
        Simple moving average forecast as fallback.
        
        Args:
            data: Time series data
            periods: Number of periods to forecast
            
        Returns:
            Dictionary with simple forecast
        """
        if data.empty:
            # Return zeros if no data
            last_date = datetime.now()
            return {
                'model': 'Simple',
                'forecasts': [
                    {
                        'date': (last_date + timedelta(days=i+1)).isoformat(),
                        'value': 0,
                        'lower_bound': 0,
                        'upper_bound': 0
                    }
                    for i in range(periods)
                ]
            }
        
        # Use moving average of last 7 days
        window = min(7, len(data))
        recent_avg = data['sales_count'].tail(window).mean()
        std_dev = data['sales_count'].tail(window).std()
        
        last_date = data['date'].max()
        
        forecasts = []
        for i in range(periods):
            forecast_date = last_date + timedelta(days=i+1)
            
            # Add slight trend if data shows growth
            if len(data) >= 3:
                recent_trend = (data['sales_count'].iloc[-1] - data['sales_count'].iloc[-3]) / 3
                forecast_value = recent_avg + (i * recent_trend)
            else:
                forecast_value = recent_avg
            
            forecasts.append({
                'date': forecast_date.isoformat(),
                'value': max(0, round(forecast_value, 0)),
                'lower_bound': max(0, round(forecast_value - 2*std_dev, 0)),
                'upper_bound': round(forecast_value + 2*std_dev, 0)
            })
        
        return {
            'model': 'Simple',
            'forecasts': forecasts,
            'model_params': {
                'method': 'moving_average',
                'window': window
            }
        }
    
    def forecast_category(self, category: str, days_ahead: int = 7, 
                         model: str = 'ensemble') -> Dict[str, Any]:
        """
        Forecast demand for a category.
        
        Args:
            category: Product category
            days_ahead: Days to forecast ahead
            model: Model to use ('arima', 'prophet', 'ensemble', 'simple')
            
        Returns:
            Forecast results
        """
        logger.info(f"Forecasting {category} for {days_ahead} days using {model}")
        
        # Prepare data
        data = self.prepare_time_series_data(category, days=14)
        
        if data.empty:
            logger.warning(f"No historical data for {category}, using simple forecast")
            return self._simple_forecast(data, days_ahead)
        
        # Select model
        if model.lower() == 'arima':
            forecast = self.forecast_arima(data, days_ahead)
        elif model.lower() == 'prophet':
            forecast = self.forecast_prophet(data, days_ahead)
        elif model.lower() == 'ensemble':
            forecast = self.forecast_ensemble(data, days_ahead)
        else:
            forecast = self._simple_forecast(data, days_ahead)
        
        # Add metadata
        forecast['category'] = category
        forecast['forecast_date'] = datetime.now().isoformat()
        forecast['historical_data_points'] = len(data)
        
        # Calculate trend
        if len(data) >= 2:
            trend = 'UP' if data['sales_count'].iloc[-1] > data['sales_count'].iloc[0] else 'DOWN'
        else:
            trend = 'STABLE'
        
        forecast['trend'] = trend
        
        return forecast
    
    def forecast_all_categories(self, days_ahead: int = 7) -> Dict[str, Dict[str, Any]]:
        """
        Forecast all product categories.
        
        Args:
            days_ahead: Days to forecast ahead
            
        Returns:
            Dictionary mapping categories to forecasts
        """
        categories = ['phones', 'laptops', 'fashion', 'home', 'food']
        forecasts = {}
        
        for category in categories:
            try:
                forecasts[category] = self.forecast_category(category, days_ahead, 'ensemble')
            except Exception as e:
                logger.error(f"Error forecasting {category}: {e}")
                forecasts[category] = {'error': str(e)}
        
        logger.info(f"Completed forecasts for {len(forecasts)} categories")
        return forecasts
    
    def detect_concept_drift(self, category: str, window_days: int = 7) -> Dict[str, Any]:
        """
        Detect if model predictions are degrading (concept drift).
        
        Args:
            category: Product category
            window_days: Days to analyze
            
        Returns:
            Drift detection results
        """
        # Get actual vs predicted data
        # For now, use simple error threshold
        # In production, would compare recent forecast accuracy
        
        data = self.prepare_time_series_data(category, days=window_days*2)
        
        if len(data) < window_days:
            return {
                'drift_detected': False,
                'reason': 'insufficient_data'
            }
        
        # Calculate variance change
        recent_data = data.tail(window_days)
        older_data = data.head(window_days)
        
        recent_var = recent_data['sales_count'].var()
        older_var = older_data['sales_count'].var()
        
        if older_var == 0:
            drift_detected = False
        else:
            var_change = abs((recent_var - older_var) / older_var)
            drift_detected = var_change > 0.5  # 50% variance change threshold
        
        return {
            'drift_detected': drift_detected,
            'variance_change': round(var_change if 'var_change' in locals() else 0, 3),
            'recommendation': 'Retrain model' if drift_detected else 'Model performing well'
        }


if __name__ == "__main__":
    # Test forecaster
    import config
    
    print("=" * 70)
    print("FORECASTING ENGINE TEST")
    print("=" * 70)
    
    db = DatabaseManager(config.DB_PATH)
    forecaster = Forecaster(db)
    
    # Test individual category
    print("\nForecasting 'phones' category for next 7 days...")
    phones_forecast = forecaster.forecast_category('phones', days_ahead=7, model='ensemble')
    
    print(f"\nCategory: {phones_forecast['category']}")
    print(f"Model: {phones_forecast['model']}")
    print(f"Trend: {phones_forecast['trend']}")
    print(f"Historical data points: {phones_forecast['historical_data_points']}")
    
    print("\nForecasts:")
    print("-" * 70)
    for fc in phones_forecast['forecasts']:
        date = datetime.fromisoformat(fc['date']).strftime('%Y-%m-%d')
        print(f"{date}: {fc['value']:.0f} units (CI: {fc['lower_bound']:.0f} - {fc['upper_bound']:.0f})")
    
    # Test all categories
    print("\n" + "=" * 70)
    print("ALL CATEGORIES FORECAST")
    print("=" * 70)
    
    all_forecasts = forecaster.forecast_all_categories(days_ahead=7)
    
    for category, forecast in all_forecasts.items():
        if 'error' in forecast:
            print(f"\n{category.upper()}: ERROR - {forecast['error']}")
        else:
            avg_forecast = sum(f['value'] for f in forecast['forecasts']) / len(forecast['forecasts'])
            print(f"\n{category.upper()}:")
            print(f"  7-day average forecast: {avg_forecast:.0f} units/day")
            print(f"  Trend: {forecast['trend']}")
            print(f"  Model: {forecast['model']}")
    
    # Test concept drift detection
    print("\n" + "=" * 70)
    print("CONCEPT DRIFT DETECTION")
    print("=" * 70)
    
    for category in ['phones', 'laptops', 'fashion']:
        drift = forecaster.detect_concept_drift(category)
        status = "DETECTED" if drift['drift_detected'] else "NOT DETECTED"
        print(f"\n{category.upper()}: Drift {status}")
        print(f"  Recommendation: {drift['recommendation']}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)

