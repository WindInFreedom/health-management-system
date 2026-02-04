"""
Health Metrics Forecasting Service - Usage Examples

This document provides examples of how to use the forecasting service
in the health management system.

Author: Health Management System Team
Created: January 2024
"""

# Example 1: Basic Forecasting
# =============================

from measurements.forecasting import forecast_metric

# Forecast systolic blood pressure for 30 days
result = forecast_metric(
    user_id=123,
    metric='systolic',
    horizon=30
)

# Result contains:
# - forecast: List of predicted values
# - confidence_lower: Lower bounds (95% confidence)
# - confidence_upper: Upper bounds (95% confidence)
# - dates: Forecast dates in ISO format
# - model_type: Which model was used
# - n_historical_points: Number of data points used

print(f"Model used: {result['model_type']}")
print(f"30-day forecast: {result['forecast']}")


# Example 2: Using Different Metrics
# ===================================

metrics = ['systolic', 'diastolic', 'heart_rate', 'blood_glucose', 'weight_kg']

for metric in metrics:
    try:
        forecast = forecast_metric(user_id=123, metric=metric, horizon=7)
        print(f"{metric}: {forecast['forecast'][0]:.2f} (day 1)")
    except RuntimeError as e:
        print(f"{metric}: No data available")


# Example 3: Using Forecast Summary
# ==================================

from measurements.forecasting import get_forecast_summary

# Get forecast with summary statistics
summary = get_forecast_summary(
    user_id=123,
    metric='weight_kg',
    horizon=30
)

print(f"Mean forecast: {summary['summary']['mean']:.2f} kg")
print(f"Trend: {summary['summary']['trend']}")
print(f"Range: {summary['summary']['min']:.2f} - {summary['summary']['max']:.2f} kg")


# Example 4: Validating Forecast Accuracy
# ========================================

from measurements.forecasting import validate_forecast_quality

# Backtest the model to see how accurate it is
validation = validate_forecast_quality(
    user_id=123,
    metric='systolic',
    test_days=7
)

print(f"Mean Absolute Error: {validation['mae']:.2f}")
print(f"Root Mean Square Error: {validation['rmse']:.2f}")
print(f"Mean Absolute Percentage Error: {validation['mape']:.2f}%")


# Example 5: Visualizing Forecasts (with matplotlib)
# ==================================================

import matplotlib.pyplot as plt
from datetime import datetime

result = forecast_metric(user_id=123, metric='systolic', horizon=30)

# Convert date strings to datetime objects
dates = [datetime.strptime(d, '%Y-%m-%d') for d in result['dates']]

# Plot forecast with confidence intervals
plt.figure(figsize=(12, 6))
plt.plot(dates, result['forecast'], label='Forecast', linewidth=2)
plt.fill_between(
    dates,
    result['confidence_lower'],
    result['confidence_upper'],
    alpha=0.3,
    label='95% Confidence Interval'
)
plt.xlabel('Date')
plt.ylabel('Systolic Blood Pressure (mmHg)')
plt.title('30-Day Blood Pressure Forecast')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('forecast.png')


# Example 6: REST API View Integration
# =====================================

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from measurements.forecasting import forecast_metric

class ForecastView(APIView):
    """API endpoint for health metric forecasting."""
    
    def get(self, request):
        """
        Get forecast for a health metric.
        
        Query parameters:
        - metric: Health metric to forecast (required)
        - horizon: Number of days to forecast (default: 30)
        """
        user_id = request.user.id
        metric = request.query_params.get('metric')
        horizon = int(request.query_params.get('horizon', 30))
        
        if not metric:
            return Response(
                {'error': 'metric parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = forecast_metric(user_id, metric, horizon)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except RuntimeError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


# Example 7: Error Handling
# ==========================

from measurements.forecasting import forecast_metric

try:
    result = forecast_metric(user_id=123, metric='systolic', horizon=30)
except ValueError as e:
    # Invalid metric or horizon
    print(f"Invalid input: {e}")
except RuntimeError as e:
    # Insufficient data or forecasting failed
    print(f"Cannot forecast: {e}")
except Exception as e:
    # Unexpected error
    print(f"Unexpected error: {e}")


# Example 8: Understanding Model Selection
# =========================================

"""
The service automatically selects the best model based on data availability:

- < 3 points: Last value method
  - Uses the most recent measurement
  - Minimal confidence interval based on variation
  
- 3-4 points: Moving average
  - Simple average with trend adjustment
  - Moderate confidence intervals
  
- 5-9 points: Linear regression
  - Fits linear trend to data
  - Confidence intervals widen with forecast distance
  
- >= 10 points: Advanced methods (ARIMA/ETS)
  - Exponential smoothing with damped trend
  - Falls back to ARIMA if ETS fails
  - Most sophisticated modeling with proper error estimates

The service always tries to use the best available method and falls back
gracefully if advanced methods fail.
"""


# Example 9: Batch Forecasting
# =============================

def forecast_all_metrics(user_id, horizon=30):
    """Forecast all available metrics for a user."""
    
    metrics = ['systolic', 'diastolic', 'heart_rate', 'blood_glucose', 'weight_kg']
    results = {}
    
    for metric in metrics:
        try:
            results[metric] = forecast_metric(user_id, metric, horizon)
        except RuntimeError:
            # Metric has no data
            results[metric] = None
    
    return results

# Usage
all_forecasts = forecast_all_metrics(user_id=123, horizon=7)

for metric, forecast in all_forecasts.items():
    if forecast:
        print(f"{metric}: {forecast['forecast'][0]:.2f} (using {forecast['model_type']})")
    else:
        print(f"{metric}: No data")


# Example 10: Custom Horizon Based on Data Quality
# =================================================

from measurements.forecasting import forecast_metric

def smart_forecast(user_id, metric, max_horizon=90):
    """
    Adjust forecast horizon based on available data.
    
    More data -> longer reliable forecast
    Less data -> shorter forecast
    """
    
    # Try a forecast to see how much data we have
    result = forecast_metric(user_id, metric, horizon=7)
    n_points = result['n_historical_points']
    
    # Adjust horizon based on data availability
    if n_points < 5:
        recommended_horizon = 7  # 1 week
    elif n_points < 10:
        recommended_horizon = 14  # 2 weeks
    elif n_points < 20:
        recommended_horizon = 30  # 1 month
    else:
        recommended_horizon = min(60, max_horizon)  # 2 months
    
    # Get forecast with recommended horizon
    return forecast_metric(user_id, metric, recommended_horizon)

# Usage
forecast = smart_forecast(user_id=123, metric='systolic')
print(f"Forecast horizon: {len(forecast['forecast'])} days")
