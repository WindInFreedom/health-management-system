# Health Metrics Forecasting Service

A lightweight, robust time series forecasting service for health metrics in the Django backend.

## Overview

This service provides time series forecasting capabilities for various health metrics, automatically selecting the best forecasting method based on data availability. It uses sophisticated statistical models (ARIMA/ETS) when sufficient data is available, with intelligent fallback to simpler methods for limited data scenarios.

## Features

- **Adaptive Model Selection**: Automatically chooses the best forecasting method based on data quantity
- **Multiple Forecasting Methods**:
  - Advanced: ARIMA and Exponential Smoothing (ETS) for rich datasets (≥10 points)
  - Linear Regression: For moderate datasets (5-9 points)
  - Moving Average: For short histories (3-4 points)
  - Last Value: For very limited data (<3 points)
- **Confidence Intervals**: Returns 95% confidence intervals for all forecasts
- **Graceful Error Handling**: Robust fallback mechanisms ensure forecasts are always possible
- **Comprehensive Documentation**: Detailed docstrings and usage examples

## Supported Metrics

- `systolic`: Systolic blood pressure (mmHg)
- `diastolic`: Diastolic blood pressure (mmHg)
- `heart_rate`: Heart rate (beats per minute)
- `blood_glucose`: Blood glucose level (mmol/L)
- `weight_kg`: Weight (kilograms)

## Installation

The required dependencies are already included in `requirements.txt`:

```
statsmodels==0.14.1
pandas==2.1.4
numpy==1.26.0
```

## Usage

### Basic Forecasting

```python
from measurements.forecasting import forecast_metric

# Forecast systolic blood pressure for 30 days
result = forecast_metric(
    user_id=123,
    metric='systolic',
    horizon=30
)

# Access results
print(f"Forecast values: {result['forecast']}")
print(f"Model used: {result['model_type']}")
print(f"Confidence lower: {result['confidence_lower']}")
print(f"Confidence upper: {result['confidence_upper']}")
print(f"Dates: {result['dates']}")
```

### Forecast with Summary Statistics

```python
from measurements.forecasting import get_forecast_summary

summary = get_forecast_summary(user_id=123, metric='weight_kg', horizon=30)

print(f"Mean forecast: {summary['summary']['mean']:.2f}")
print(f"Trend: {summary['summary']['trend']}")  # 'increasing', 'decreasing', or 'stable'
```

### Validate Forecast Accuracy

```python
from measurements.forecasting import validate_forecast_quality

# Backtest the model using the last 7 days
validation = validate_forecast_quality(user_id=123, metric='systolic', test_days=7)

print(f"MAE: {validation['mae']:.2f}")
print(f"RMSE: {validation['rmse']:.2f}")
print(f"MAPE: {validation['mape']:.2f}%")
```

## Function Reference

### `forecast_metric(user_id, metric, horizon=30)`

Primary forecasting function.

**Parameters:**
- `user_id` (int): User ID to forecast metrics for
- `metric` (str): Metric name (see supported metrics above)
- `horizon` (int): Number of days to forecast (default: 30, max: 90)

**Returns:**
Dict with keys:
- `forecast`: List of forecasted values
- `confidence_lower`: List of lower confidence bounds (95% CI)
- `confidence_upper`: List of upper confidence bounds (95% CI)
- `dates`: List of forecast dates (ISO format strings)
- `model_type`: String indicating which model was used
- `n_historical_points`: Number of historical data points used
- `message`: Optional message about data quality or limitations

**Raises:**
- `ValueError`: If metric is not supported or horizon is invalid
- `RuntimeError`: If insufficient data is available for forecasting

### `get_forecast_summary(user_id, metric, horizon=30)`

Get forecast with additional summary statistics.

**Returns:**
Same as `forecast_metric` plus a `summary` key containing:
- `mean`: Mean of forecasted values
- `median`: Median of forecasted values
- `min`: Minimum forecasted value
- `max`: Maximum forecasted value
- `trend`: Trend direction ('increasing', 'decreasing', or 'stable')

### `validate_forecast_quality(user_id, metric, test_days=7)`

Validate forecast quality using backtesting.

**Parameters:**
- `user_id` (int): User ID
- `metric` (str): Metric name
- `test_days` (int): Number of days to use for validation

**Returns:**
Dict with validation metrics:
- `mae`: Mean Absolute Error
- `rmse`: Root Mean Square Error
- `mape`: Mean Absolute Percentage Error
- `n_train`: Number of training points used
- `n_test`: Number of test points used
- `model_type`: Model type used for validation

## Model Selection Logic

The service automatically selects the appropriate forecasting method:

| Data Points | Method | Description |
|-------------|--------|-------------|
| < 3 | Last Value | Uses most recent measurement with minimal variation |
| 3-4 | Moving Average | Simple average with trend adjustment |
| 5-9 | Linear Regression | Fits linear trend with widening confidence intervals |
| ≥ 10 | Advanced (ETS/ARIMA) | Exponential smoothing or ARIMA with fallback |

## Error Handling

The service is designed to handle errors gracefully:

```python
try:
    result = forecast_metric(user_id=123, metric='systolic', horizon=30)
except ValueError as e:
    # Invalid metric or horizon
    print(f"Invalid input: {e}")
except RuntimeError as e:
    # Insufficient data or forecasting failed
    print(f"Cannot forecast: {e}")
```

## Examples

See `forecasting_examples.py` for comprehensive usage examples including:
- Basic forecasting for different metrics
- REST API integration
- Batch forecasting for multiple metrics
- Visualization with matplotlib
- Smart horizon adjustment based on data quality

## Implementation Details

### Data Preparation

- Historical measurements are fetched from the `Measurement` model
- Multiple measurements on the same day are aggregated (mean)
- Missing values are handled appropriately
- Data is sorted chronologically

### Confidence Intervals

- 95% confidence intervals are provided for all forecasts
- Intervals widen appropriately with forecast distance
- Based on residual standard error for regression methods
- Based on model estimates for advanced methods

### Performance

- Lightweight: Uses efficient pandas operations
- Fast: Model fitting typically takes < 1 second
- Scalable: Handles users with thousands of measurements

## Limitations

- Maximum forecast horizon: 90 days
- Seasonality: Not explicitly modeled (insufficient data for most users)
- Missing data: Requires at least 1 historical measurement
- Outliers: Not automatically detected or removed

## Future Enhancements

Potential improvements for future versions:

1. **Outlier Detection**: Automatic detection and handling of anomalous measurements
2. **Multiple Time Series**: Joint forecasting of related metrics
3. **Seasonal Models**: Support for weekly/monthly patterns when sufficient data exists
4. **Feature Engineering**: Incorporate external factors (age, medication, etc.)
5. **Ensemble Methods**: Combine multiple models for improved accuracy
6. **Real-time Updates**: Incremental model updates as new data arrives

## Testing

The service includes comprehensive tests covering:
- All forecasting methods
- Edge cases (single point, constant values, etc.)
- Confidence interval properties
- Date formatting
- Error handling

Run tests with:
```bash
python test_forecasting_unit.py
```

## Contributing

When modifying the forecasting service:

1. Maintain backward compatibility with the existing API
2. Add comprehensive docstrings for new functions
3. Include error handling for edge cases
4. Test with various data sizes and patterns
5. Update this documentation

## License

Part of the Health Management System project.

## Support

For questions or issues, please contact the development team or create an issue in the project repository.
