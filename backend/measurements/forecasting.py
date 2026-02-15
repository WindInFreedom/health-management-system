"""
Health Metrics Forecasting Service

This module provides time series forecasting capabilities for health metrics
using statsmodels (ARIMA/ETS) with fallback to simpler methods for limited data.

Supported metrics:
- systolic: Systolic blood pressure
- diastolic: Diastolic blood pressure
- heart_rate: Heart rate in beats per minute
- blood_glucose: Blood glucose level in mmol/L
- weight_kg: Weight in kilograms
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

import numpy as np
import pandas as pd
from django.db.models import Q

logger = logging.getLogger(__name__)


def forecast_metric(user_id: int, metric: str, horizon: int = 30) -> Dict:
    """
    Forecast a health metric for a user using time series analysis.
    
    This function attempts to use sophisticated forecasting models
    when sufficient data is available, and falls back to simpler methods
    for limited data.
    
    Args:
        user_id: User ID to forecast metrics for
        metric: Metric name ('systolic', 'diastolic', 'heart_rate', 'blood_glucose', 'weight_kg')
        horizon: Number of days to forecast (default: 30, max: 90)
    
    Returns:
        Dict with keys:
            - forecast: List of forecasted values
            - confidence_lower: List of lower confidence bounds (95% CI)
            - confidence_upper: List of upper confidence bounds (95% CI)
            - dates: List of forecast dates (ISO format strings)
            - model_type: String indicating which model was used
            - message: Optional message about data quality or limitations
    
    Raises:
        ValueError: If metric is not supported or horizon is invalid
        RuntimeError: If insufficient data is available for forecasting
    """
    # Validate inputs
    supported_metrics = ['systolic', 'diastolic', 'heart_rate', 'blood_glucose', 'weight_kg']
    if metric not in supported_metrics:
        raise ValueError(f"Unsupported metric '{metric}'. Must be one of: {supported_metrics}")
    
    if not 1 <= horizon <= 90:
        raise ValueError(f"Horizon must be between 1 and 90 days, got {horizon}")
    
    # Import Measurement model here to avoid circular imports
    from measurements.models import Measurement
    
    # Fetch historical data
    try:
        historical_data = _fetch_historical_data(user_id, metric, Measurement)
    except Exception as e:
        logger.error(f"Error fetching historical data for user {user_id}, metric {metric}: {e}")
        raise RuntimeError(f"Failed to fetch historical data: {e}")
    
    if len(historical_data) == 0:
        raise RuntimeError(f"No historical data available for metric '{metric}'")
    
    # Choose forecasting method based on data availability and metric type
    n_points = len(historical_data)
    
    try:
        if n_points < 3:
            # Very limited data - use last value with minimal variation
            result = _forecast_last_value(historical_data, horizon)
            result['message'] = f"Limited data ({n_points} points). Using last value method."
            
        elif n_points < 5:
            # Short history - use moving average
            result = _forecast_moving_average(historical_data, horizon)
            result['message'] = f"Short history ({n_points} points). Using moving average."
            
        elif n_points < 10:
            # Moderate history - use linear regression
            result = _forecast_linear_regression(historical_data, horizon)
            result['message'] = f"Moderate history ({n_points} points). Using linear regression."
            
        else:
            # Sufficient data - choose model based on metric type
            try:
                # 根据指标类型选择合适的模型
                if metric in ['heart_rate']:  # 短期平稳指标（如心率、脉搏）
                    # 使用指数平滑（Holt-Winters）
                    result = _forecast_advanced(historical_data, horizon, model_type='exponential_smoothing')
                    result['model_type'] = 'Exponential Smoothing'  # 短期平稳指标推荐模型
                elif metric in ['weight_kg']:  # 有趋势或周期性指标（如体重）
                    # 使用LSTM
                    try:
                        result = _forecast_lstm(historical_data, horizon)
                        result['model_type'] = 'LSTM'  # 有趋势指标推荐模型
                    except Exception as e:
                        logger.warning(f"LSTM forecasting failed for user {user_id}, metric {metric}: {e}")
                        # Fallback to exponential smoothing
                        result = _forecast_advanced(historical_data, horizon, model_type='exponential_smoothing')
                        result['model_type'] = 'Exponential Smoothing (Fallback)'
                elif metric in ['systolic', 'diastolic', 'blood_glucose']:  # 血压血糖
                    # 使用LSTM + Attention
                    try:
                        result = _forecast_lstm_attention(historical_data, horizon)
                        result['model_type'] = 'LSTM + Attention'  # 血压血糖推荐模型
                    except Exception as e:
                        logger.warning(f"LSTM + Attention forecasting failed for user {user_id}, metric {metric}: {e}")
                        # Fallback to LSTM
                        try:
                            result = _forecast_lstm(historical_data, horizon)
                            result['model_type'] = 'LSTM (Fallback)'
                        except Exception as e2:
                            logger.warning(f"LSTM forecasting also failed: {e2}")
                            # Fallback to exponential smoothing
                            result = _forecast_advanced(historical_data, horizon, model_type='exponential_smoothing')
                            result['model_type'] = 'Exponential Smoothing (Fallback)'
                else:
                    # 默认使用高级方法
                    result = _forecast_advanced(historical_data, horizon)
            except Exception as e:
                logger.warning(f"Advanced forecasting failed for user {user_id}, metric {metric}: {e}")
                # Fallback to linear regression
                result = _forecast_linear_regression(historical_data, horizon)
                result['message'] = "Advanced methods failed. Using linear regression fallback."
        
        # Add metadata
        result['n_historical_points'] = n_points
        result['metric'] = metric
        
        return result
        
    except Exception as e:
        logger.error(f"Forecasting failed for user {user_id}, metric {metric}: {e}")
        raise RuntimeError(f"Forecasting failed: {e}")


def _fetch_historical_data(user_id: int, metric: str, Measurement) -> pd.DataFrame:
    """
    Fetch and prepare historical measurement data for forecasting.
    
    Args:
        user_id: User ID
        metric: Metric field name
        Measurement: Measurement model class
    
    Returns:
        DataFrame with 'date' and 'value' columns, sorted by date
    """
    # Build query to get measurements with non-null values for the metric
    filter_kwargs = {f'{metric}__isnull': False}
    
    measurements = Measurement.objects.filter(
        user_id=user_id,
        **filter_kwargs
    ).order_by('measured_at').values('measured_at', metric)
    
    # Convert to DataFrame
    df = pd.DataFrame(list(measurements))
    
    if df.empty:
        return df
    
    # Rename columns for consistency
    df.columns = ['date', 'value']
    
    # Convert to appropriate types
    df['date'] = pd.to_datetime(df['date'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    # Remove any NaN values that might have crept in
    df = df.dropna()
    
    # Aggregate multiple measurements on the same day (take mean)
    df = df.groupby(df['date'].dt.date).agg({'value': 'mean'}).reset_index()
    df['date'] = pd.to_datetime(df['date'])
    
    return df


def _forecast_last_value(df: pd.DataFrame, horizon: int) -> Dict:
    """
    Forecast using the last observed value with minimal uncertainty.
    
    Used when there's very limited data (< 3 points).
    
    Args:
        df: DataFrame with historical data
        horizon: Number of days to forecast
    
    Returns:
        Forecast dictionary
    """
    last_value = df['value'].iloc[-1]
    last_date = df['date'].iloc[-1]
    
    # Small confidence interval based on recent variation
    if len(df) > 1:
        std = df['value'].std()
    else:
        # Use 5% of the value as uncertainty if only one point
        std = abs(last_value * 0.05)
    
    # Generate forecast dates
    forecast_dates = [last_date + timedelta(days=i+1) for i in range(horizon)]
    
    # Constant forecast
    forecast = [last_value] * horizon
    confidence_lower = [last_value - 1.96 * std] * horizon
    confidence_upper = [last_value + 1.96 * std] * horizon
    
    return {
        'forecast': forecast,
        'confidence_lower': confidence_lower,
        'confidence_upper': confidence_upper,
        'dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
        'model_type': 'last_value'
    }


def _forecast_moving_average(df: pd.DataFrame, horizon: int) -> Dict:
    """
    Forecast using moving average with trend adjustment.
    
    Used for short history (3-4 points).
    
    Args:
        df: DataFrame with historical data
        horizon: Number of days to forecast
    
    Returns:
        Forecast dictionary
    """
    values = df['value'].values
    last_date = df['date'].iloc[-1]
    
    # Calculate simple moving average
    ma = np.mean(values)
    
    # Estimate trend from first half to second half
    if len(values) >= 3:
        mid = len(values) // 2
        first_half_mean = np.mean(values[:mid])
        second_half_mean = np.mean(values[mid:])
        trend = (second_half_mean - first_half_mean) / mid
    else:
        trend = 0
    
    # Standard deviation for confidence intervals
    std = np.std(values)
    
    # Generate forecast dates
    forecast_dates = [last_date + timedelta(days=i+1) for i in range(horizon)]
    
    # Generate forecast with trend
    forecast = [ma + trend * (i + 1) for i in range(horizon)]
    
    # Confidence intervals widen slightly with time
    confidence_lower = [forecast[i] - 1.96 * std * (1 + 0.01 * i) for i in range(horizon)]
    confidence_upper = [forecast[i] + 1.96 * std * (1 + 0.01 * i) for i in range(horizon)]
    
    return {
        'forecast': forecast,
        'confidence_lower': confidence_lower,
        'confidence_upper': confidence_upper,
        'dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
        'model_type': 'moving_average'
    }


def _forecast_linear_regression(df: pd.DataFrame, horizon: int) -> Dict:
    """
    Forecast using linear regression.
    
    Used for moderate history (5-9 points) or as fallback for failed advanced methods.
    
    Args:
        df: DataFrame with historical data
        horizon: Number of days to forecast
    
    Returns:
        Forecast dictionary
    """
    # Prepare data for linear regression
    df = df.copy()
    df['days'] = (df['date'] - df['date'].min()).dt.days
    
    X = df['days'].values
    y = df['value'].values
    
    # Fit linear regression using numpy
    coefficients = np.polyfit(X, y, 1)
    slope, intercept = coefficients
    
    # Calculate residual standard error
    y_pred = slope * X + intercept
    residuals = y - y_pred
    mse = np.mean(residuals ** 2)
    rmse = np.sqrt(mse)
    
    # Generate forecast
    last_date = df['date'].iloc[-1]
    last_day = df['days'].iloc[-1]
    
    forecast_dates = [last_date + timedelta(days=i+1) for i in range(horizon)]
    forecast_days = [last_day + i + 1 for i in range(horizon)]
    
    forecast = [slope * d + intercept for d in forecast_days]
    
    # Confidence intervals widen with distance from the data
    # Using approximate formula for prediction intervals
    n = len(X)
    mean_x = np.mean(X)
    ss_x = np.sum((X - mean_x) ** 2)
    
    confidence_lower = []
    confidence_upper = []
    
    for i, d in enumerate(forecast_days):
        # Standard error of prediction
        se = rmse * np.sqrt(1 + 1/n + (d - mean_x)**2 / ss_x)
        confidence_lower.append(forecast[i] - 1.96 * se)
        confidence_upper.append(forecast[i] + 1.96 * se)
    
    return {
        'forecast': forecast,
        'confidence_lower': confidence_lower,
        'confidence_upper': confidence_upper,
        'dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
        'model_type': 'linear_regression'
    }


def _forecast_advanced(df: pd.DataFrame, horizon: int, model_type='auto') -> Dict:
    """
    Forecast using advanced time series models.
    
    Used when sufficient data is available (>= 10 points).
    
    Args:
        df: DataFrame with historical data
        horizon: Number of days to forecast
        model_type: Type of model to use ('auto', 'arima', 'exponential_smoothing', 'lstm', 'prophet')
    
    Returns:
        Forecast dictionary
    
    Raises:
        Exception: If model fitting fails
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.arima.model import ARIMA
    
    values = df['value'].values
    last_date = df['date'].iloc[-1]
    
    # 根据指定的模型类型选择预测方法
    if model_type == 'arima' or (model_type == 'auto' and len(values) >= 15):
        # 尝试ARIMA模型
        try:
            # Use auto-selected order with simple (1,1,1) as default
            model = ARIMA(values, order=(1, 1, 1))
            fitted_model = model.fit()
            
            # Generate forecast with confidence intervals
            forecast_result = fitted_model.forecast(steps=horizon)
            forecast = forecast_result.tolist()
            
            # Get confidence intervals
            forecast_obj = fitted_model.get_forecast(steps=horizon)
            conf_int = forecast_obj.conf_int(alpha=0.05)
            
            confidence_lower = conf_int.iloc[:, 0].tolist()
            confidence_upper = conf_int.iloc[:, 1].tolist()
            
            model_type = 'arima'
            
        except Exception as e:
            logger.debug(f"ARIMA failed, falling back to exponential smoothing: {e}")
            # 回退到指数平滑
            model = ExponentialSmoothing(
                values,
                trend='add',
                seasonal=None,  # Not enough data for seasonality
                damped_trend=True
            )
            fitted_model = model.fit(optimized=True)
            
            # Generate forecast
            forecast_result = fitted_model.forecast(steps=horizon)
            forecast = forecast_result.tolist()
            
            # Get prediction intervals (simulate if not directly available)
            # Use residuals to estimate confidence intervals
            residuals = fitted_model.fittedvalues - values[:-1] if len(fitted_model.fittedvalues) < len(values) else fitted_model.fittedvalues - values
            residual_std = np.std(residuals)
            
            confidence_lower = [forecast[i] - 1.96 * residual_std * np.sqrt(i + 1) for i in range(horizon)]
            confidence_upper = [forecast[i] + 1.96 * residual_std * np.sqrt(i + 1) for i in range(horizon)]
            
            model_type = 'exponential_smoothing'
            
    elif model_type == 'prophet' or (model_type == 'auto' and len(values) >= 20):
        # 尝试Prophet模型（如果安装了）
        try:
            from prophet import Prophet
            
            # Prepare data for Prophet
            prophet_df = df.rename(columns={'date': 'ds', 'value': 'y'})
            
            # Fit Prophet model
            model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
            model.fit(prophet_df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=horizon, freq='D')
            
            # Generate forecast
            forecast_result = model.predict(future)
            
            # Extract forecast values and confidence intervals
            forecast = forecast_result['yhat'].tail(horizon).tolist()
            confidence_lower = forecast_result['yhat_lower'].tail(horizon).tolist()
            confidence_upper = forecast_result['yhat_upper'].tail(horizon).tolist()
            
            model_type = 'prophet'
            
        except ImportError:
            logger.debug("Prophet not installed, falling back to exponential smoothing")
            # 回退到指数平滑
            model = ExponentialSmoothing(
                values,
                trend='add',
                seasonal=None,  # Not enough data for seasonality
                damped_trend=True
            )
            fitted_model = model.fit(optimized=True)
            
            # Generate forecast
            forecast_result = fitted_model.forecast(steps=horizon)
            forecast = forecast_result.tolist()
            
            # Get prediction intervals (simulate if not directly available)
            # Use residuals to estimate confidence intervals
            residuals = fitted_model.fittedvalues - values[:-1] if len(fitted_model.fittedvalues) < len(values) else fitted_model.fittedvalues - values
            residual_std = np.std(residuals)
            
            confidence_lower = [forecast[i] - 1.96 * residual_std * np.sqrt(i + 1) for i in range(horizon)]
            confidence_upper = [forecast[i] + 1.96 * residual_std * np.sqrt(i + 1) for i in range(horizon)]
            
            model_type = 'exponential_smoothing'
            
        except Exception as e:
            logger.debug(f"Prophet failed, falling back to exponential smoothing: {e}")
            # 回退到指数平滑
            model = ExponentialSmoothing(
                values,
                trend='add',
                seasonal=None,  # Not enough data for seasonality
                damped_trend=True
            )
            fitted_model = model.fit(optimized=True)
            
            # Generate forecast
            forecast_result = fitted_model.forecast(steps=horizon)
            forecast = forecast_result.tolist()
            
            # Get prediction intervals (simulate if not directly available)
            # Use residuals to estimate confidence intervals
            residuals = fitted_model.fittedvalues - values[:-1] if len(fitted_model.fittedvalues) < len(values) else fitted_model.fittedvalues - values
            residual_std = np.std(residuals)
            
            confidence_lower = [forecast[i] - 1.96 * residual_std * np.sqrt(i + 1) for i in range(horizon)]
            confidence_upper = [forecast[i] + 1.96 * residual_std * np.sqrt(i + 1) for i in range(horizon)]
            
            model_type = 'exponential_smoothing'
            
    else:
        # 默认使用指数平滑（更稳健）
        try:
            model = ExponentialSmoothing(
                values,
                trend='add',
                seasonal=None,  # Not enough data for seasonality
                damped_trend=True
            )
            fitted_model = model.fit(optimized=True)
            
            # Generate forecast
            forecast_result = fitted_model.forecast(steps=horizon)
            forecast = forecast_result.tolist()
            
            # Get prediction intervals (simulate if not directly available)
            # Use residuals to estimate confidence intervals
            residuals = fitted_model.fittedvalues - values[:-1] if len(fitted_model.fittedvalues) < len(values) else fitted_model.fittedvalues - values
            residual_std = np.std(residuals)
            
            confidence_lower = [forecast[i] - 1.96 * residual_std * np.sqrt(i + 1) for i in range(horizon)]
            confidence_upper = [forecast[i] + 1.96 * residual_std * np.sqrt(i + 1) for i in range(horizon)]
            
            model_type = 'exponential_smoothing'
            
        except Exception as e:
            logger.debug(f"Exponential smoothing failed, trying ARIMA: {e}")
            
            # Try ARIMA as alternative
            try:
                # Use auto-selected order with simple (1,1,1) as default
                model = ARIMA(values, order=(1, 1, 1))
                fitted_model = model.fit()
                
                # Generate forecast with confidence intervals
                forecast_result = fitted_model.forecast(steps=horizon)
                forecast = forecast_result.tolist()
                
                # Get confidence intervals
                forecast_obj = fitted_model.get_forecast(steps=horizon)
                conf_int = forecast_obj.conf_int(alpha=0.05)
                
                confidence_lower = conf_int.iloc[:, 0].tolist()
                confidence_upper = conf_int.iloc[:, 1].tolist()
                
                model_type = 'arima'
                
            except Exception as e2:
                logger.debug(f"ARIMA also failed: {e2}")
                raise Exception(f"Both ETS and ARIMA failed: ETS={e}, ARIMA={e2}")
    
    # Generate forecast dates
    forecast_dates = [last_date + timedelta(days=i+1) for i in range(horizon)]
    
    return {
        'forecast': forecast,
        'confidence_lower': confidence_lower,
        'confidence_upper': confidence_upper,
        'dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
        'model_type': model_type
    }


def get_forecast_summary(user_id: int, metric: str, horizon: int = 30) -> Dict:
    """
    Get a forecast with additional summary statistics.
    
    This is a convenience function that adds summary statistics to the
    standard forecast output.
    
    Args:
        user_id: User ID
        metric: Metric name
        horizon: Number of days to forecast
    
    Returns:
        Forecast dictionary with additional 'summary' key containing statistics
    """
    result = forecast_metric(user_id, metric, horizon)
    
    # Add summary statistics
    forecast_values = result['forecast']
    result['summary'] = {
        'mean': float(np.mean(forecast_values)),
        'median': float(np.median(forecast_values)),
        'min': float(np.min(forecast_values)),
        'max': float(np.max(forecast_values)),
        'trend': 'increasing' if forecast_values[-1] > forecast_values[0] else 
                 'decreasing' if forecast_values[-1] < forecast_values[0] else 'stable'
    }
    
    return result


def validate_forecast_quality(user_id: int, metric: str, test_days: int = 7) -> Dict:
    """
    Validate forecast quality using backtesting.
    
    This function creates a forecast for historical data and compares it
    to actual values to estimate forecast accuracy.
    
    Args:
        user_id: User ID
        metric: Metric name
        test_days: Number of days to use for validation
    
    Returns:
        Dictionary with validation metrics (MAE, RMSE, MAPE)
    """
    from measurements.models import Measurement
    
    # Fetch all historical data
    df = _fetch_historical_data(user_id, metric, Measurement)
    
    if len(df) < test_days + 5:
        raise RuntimeError(f"Insufficient data for validation (need at least {test_days + 5} points)")
    
    # Split data into train and test
    train_df = df.iloc[:-test_days]
    test_df = df.iloc[-test_days:]
    
    # Create forecast using training data
    # Temporarily modify the dataframe for forecasting
    last_train_date = train_df['date'].iloc[-1]
    
    # Determine which method to use based on training data size
    n_points = len(train_df)
    if n_points >= 10:
        forecast_result = _forecast_advanced(train_df, test_days)
    elif n_points >= 5:
        forecast_result = _forecast_linear_regression(train_df, test_days)
    elif n_points >= 3:
        forecast_result = _forecast_moving_average(train_df, test_days)
    else:
        forecast_result = _forecast_last_value(train_df, test_days)
    
    # Compare forecast to actual values
    forecast_values = np.array(forecast_result['forecast'][:len(test_df)])
    actual_values = test_df['value'].values
    
    # Calculate error metrics
    errors = actual_values - forecast_values
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    
    # MAPE (avoid division by zero)
    mape = float(np.mean(np.abs(errors / (actual_values + 1e-10))) * 100)
    
    return {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'n_train': len(train_df),
        'n_test': len(test_df),
        'model_type': forecast_result['model_type']
    }


def _create_sequences(data, seq_length):
    """
    Create sequences for LSTM input
    
    Args:
        data: Array of values
        seq_length: Length of each sequence
    
    Returns:
        X: Input sequences
        y: Target values
    """
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)


def _forecast_lstm(df, horizon):
    """
    Forecast using LSTM model
    
    Args:
        df: DataFrame with historical data
        horizon: Number of days to forecast
    
    Returns:
        Forecast dictionary
    """
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    
    values = df['value'].values
    last_date = df['date'].iloc[-1]
    
    # Normalize data
    mean = np.mean(values)
    std = np.std(values)
    normalized_values = (values - mean) / std
    
    # Create sequences
    seq_length = 7  # Use 7 days of history
    X, y = _create_sequences(normalized_values, seq_length)
    
    # Reshape for LSTM input (samples, time steps, features)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    
    # Build LSTM model
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(seq_length, 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(50))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    
    # Compile model
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    
    # Train model
    model.fit(X, y, epochs=50, batch_size=32, verbose=0)
    
    # Generate forecast
    forecast = []
    current_seq = normalized_values[-seq_length:].reshape((1, seq_length, 1))
    
    for _ in range(horizon):
        next_val = model.predict(current_seq, verbose=0)[0][0]
        forecast.append(next_val)
        # Update sequence for next prediction
        current_seq = np.roll(current_seq, -1, axis=1)
        current_seq[0, -1, 0] = next_val
    
    # Denormalize forecast
    forecast = np.array(forecast) * std + mean
    
    # Generate forecast dates
    forecast_dates = [last_date + timedelta(days=i+1) for i in range(horizon)]
    
    # Calculate confidence intervals (simple approach using standard deviation)
    residual_std = std * 0.1  # Assume 10% of data std as prediction uncertainty
    confidence_lower = forecast - 1.96 * residual_std
    confidence_upper = forecast + 1.96 * residual_std
    
    return {
        'forecast': forecast.tolist(),
        'confidence_lower': confidence_lower.tolist(),
        'confidence_upper': confidence_upper.tolist(),
        'dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
        'model_type': 'LSTM'
    }


def _forecast_lstm_attention(df, horizon):
    """
    Forecast using LSTM with Attention mechanism
    
    Args:
        df: DataFrame with historical data
        horizon: Number of days to forecast
    
    Returns:
        Forecast dictionary
    """
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import Input, LSTM, Dense, Dropout, Attention
    from tensorflow.keras.optimizers import Adam
    
    values = df['value'].values
    last_date = df['date'].iloc[-1]
    
    # Normalize data
    mean = np.mean(values)
    std = np.std(values)
    normalized_values = (values - mean) / std
    
    # Create sequences
    seq_length = 10  # Use 10 days of history for attention
    X, y = _create_sequences(normalized_values, seq_length)
    
    # Reshape for LSTM input (samples, time steps, features)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    
    # Build LSTM with Attention model
    inputs = Input(shape=(seq_length, 1))
    
    # LSTM layers
    lstm_out = LSTM(64, return_sequences=True)(inputs)
    lstm_out = Dropout(0.2)(lstm_out)
    lstm_out = LSTM(64, return_sequences=True)(lstm_out)
    lstm_out = Dropout(0.2)(lstm_out)
    
    # Attention mechanism
    attention = Attention()([lstm_out, lstm_out])
    
    # Flatten and dense layers
    attention_flat = Dense(32, activation='relu')(attention)
    output = Dense(1)(attention_flat)
    
    # Create model
    model = Model(inputs=inputs, outputs=output)
    
    # Compile model
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    
    # Train model
    model.fit(X, y, epochs=50, batch_size=32, verbose=0)
    
    # Generate forecast
    forecast = []
    current_seq = normalized_values[-seq_length:].reshape((1, seq_length, 1))
    
    for _ in range(horizon):
        next_val = model.predict(current_seq, verbose=0)[0][0]
        forecast.append(next_val)
        # Update sequence for next prediction
        current_seq = np.roll(current_seq, -1, axis=1)
        current_seq[0, -1, 0] = next_val
    
    # Denormalize forecast
    forecast = np.array(forecast) * std + mean
    
    # Generate forecast dates
    forecast_dates = [last_date + timedelta(days=i+1) for i in range(horizon)]
    
    # Calculate confidence intervals (simple approach using standard deviation)
    residual_std = std * 0.08  # Assume 8% of data std as prediction uncertainty (more accurate with attention)
    confidence_lower = forecast - 1.96 * residual_std
    confidence_upper = forecast + 1.96 * residual_std
    
    return {
        'forecast': forecast.tolist(),
        'confidence_lower': confidence_lower.tolist(),
        'confidence_upper': confidence_upper.tolist(),
        'dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
        'model_type': 'LSTM + Attention'
    }
