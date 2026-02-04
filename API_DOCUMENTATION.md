# API Documentation

## Base URL
- Development: `http://localhost:8000/api/`
- Production: Configure in environment variables

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Authentication Endpoints

#### Login
```http
POST /auth/login/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "role": "user"
  }
}
```

#### Register
```http
POST /auth/register/
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "password2": "password123"
}
```

#### Change Password
```http
POST /auth/change-password/
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "oldpass123",
  "new_password": "newpass123",
  "confirm_password": "newpass123"
}
```

## User Profile

### Get Current User
```http
GET /users/me/
Authorization: Bearer <token>
```

### Get/Update Profile
```http
GET /profile/me/
Authorization: Bearer <token>
```

```http
PUT /profile/me/
Authorization: Bearer <token>
Content-Type: application/json

{
  "age": 30,
  "gender": "M",
  "blood_type": "A",
  "height_cm": 175.5,
  "weight_baseline_kg": 70.0
}
```

## Health Measurements

### List Measurements
```http
GET /measurements/?ordering=measured_at
Authorization: Bearer <token>
```

**Query Parameters**:
- `ordering`: Sort field (e.g., `measured_at`, `-measured_at`)
- `page`: Page number
- `page_size`: Results per page

### Create Measurement
```http
POST /measurements/
Authorization: Bearer <token>
Content-Type: application/json

{
  "measured_at": "2024-02-04T10:30:00Z",
  "weight_kg": 70.5,
  "systolic": 120,
  "diastolic": 80,
  "heart_rate": 72,
  "blood_glucose": 5.5,
  "notes": "Morning measurement"
}
```

### Update Measurement
```http
PUT /measurements/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "measured_at": "2024-02-04T10:30:00Z",
  "weight_kg": 71.0,
  "systolic": 118,
  "diastolic": 78,
  "heart_rate": 70,
  "blood_glucose": 5.3,
  "notes": "Updated measurement"
}
```

### Delete Measurement
```http
DELETE /measurements/{id}/
Authorization: Bearer <token>
```

## Health Report

### Generate Health Report
```http
GET /health-report/?days=30
Authorization: Bearer <token>
```

**Query Parameters**:
- `days`: Number of days to analyze (default: 30)

**Response**:
```json
{
  "overall_score": 75.5,
  "overall_status": "good",
  "overall_message": "您的整体健康状况良好",
  "overall_suggestions": [
    "注意改善评分较低的指标",
    "保持健康生活方式"
  ],
  "dimensions": {
    "bmi": {
      "score": 85.0,
      "value": 23.2,
      "status": "good",
      "message": "您的BMI为 23.2",
      "suggestions": ["保持良好的体重管理"]
    },
    "blood_pressure": {
      "score": 90.0,
      "value": {"systolic": 118, "diastolic": 78},
      "status": "excellent",
      "message": "平均血压: 118/78 mmHg",
      "suggestions": ["血压控制良好，继续保持"]
    },
    "heart_rate": {
      "score": 80.0,
      "value": 72.0,
      "status": "good",
      "message": "平均心率: 72 bpm",
      "suggestions": ["心率正常，保持规律运动"]
    },
    "blood_glucose": {
      "score": 70.0,
      "value": 6.2,
      "status": "moderate",
      "message": "平均血糖: 6.2 mmol/L",
      "suggestions": ["控制碳水化合物摄入", "增加膳食纤维"]
    },
    "sleep_quality": {
      "score": 60.0,
      "value": 6.5,
      "status": "moderate",
      "message": "平均睡眠时长: 6.5 小时",
      "suggestions": ["建立规律作息", "睡前避免使用电子设备"]
    },
    "mood_index": {
      "score": 75.0,
      "value": 7.5,
      "status": "good",
      "message": "平均心情指数: 7.5/10",
      "suggestions": ["保持积极心态"]
    }
  },
  "evaluation_period_days": 30,
  "evaluated_at": "2024-02-04T10:30:00Z"
}
```

### Get Report for User (Admin/Doctor)
```http
GET /health-report/{user_id}/?days=30
Authorization: Bearer <token>
```

## Health Forecasting

### Forecast Metric
```http
GET /forecast/?metric=systolic&horizon=30
Authorization: Bearer <token>
```

**Query Parameters**:
- `metric`: Metric to forecast (`systolic`, `diastolic`, `heart_rate`, `blood_glucose`, `weight_kg`)
- `horizon`: Days to forecast (1-90, default: 30)

**Response**:
```json
{
  "metric": "systolic",
  "horizon": 30,
  "model_type": "exponential_smoothing",
  "forecast": [120.5, 119.8, 119.2, ...],
  "confidence_lower": [115.0, 114.5, 114.0, ...],
  "confidence_upper": [126.0, 125.1, 124.4, ...],
  "dates": ["2024-02-05", "2024-02-06", "2024-02-07", ...],
  "historical_data": {
    "dates": ["2024-01-05", "2024-01-12", ...],
    "values": [122.0, 120.0, ...]
  }
}
```

## Medication Logs

### List Medications
```http
GET /medications/
Authorization: Bearer <token>
```

### Create Medication
```http
POST /medications/
Authorization: Bearer <token>
Content-Type: application/json

{
  "medication_name": "Aspirin",
  "dosage": "100mg",
  "frequency": "每日1次",
  "start_date": "2024-02-01",
  "end_date": "2024-03-01",
  "notes": "早餐后服用"
}
```

### Update Medication
```http
PUT /medications/{id}/
Authorization: Bearer <token>
Content-Type: application/json
```

### Delete Medication
```http
DELETE /medications/{id}/
Authorization: Bearer <token>
```

## Sleep Logs

### List Sleep Logs
```http
GET /sleep-logs/
Authorization: Bearer <token>
```

### Create Sleep Log
```http
POST /sleep-logs/
Authorization: Bearer <token>
Content-Type: application/json

{
  "sleep_date": "2024-02-04",
  "start_time": "2024-02-03T23:00:00Z",
  "end_time": "2024-02-04T07:00:00Z",
  "quality_rating": 8,
  "notes": "Good sleep"
}
```
**Note**: `duration_minutes` is auto-calculated from start_time and end_time.

### Update Sleep Log
```http
PUT /sleep-logs/{id}/
Authorization: Bearer <token>
Content-Type: application/json
```

### Delete Sleep Log
```http
DELETE /sleep-logs/{id}/
Authorization: Bearer <token>
```

## Mood Logs

### List Mood Logs
```http
GET /mood-logs/
Authorization: Bearer <token>
```

### Create Mood Log
```http
POST /mood-logs/
Authorization: Bearer <token>
Content-Type: application/json

{
  "log_date": "2024-02-04",
  "mood_rating": 8,
  "notes": "Feeling great today"
}
```
**Note**: Only one mood log per user per day is allowed.

### Update Mood Log
```http
PUT /mood-logs/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "mood_rating": 7,
  "notes": "Updated mood"
}
```

### Delete Mood Log
```http
DELETE /mood-logs/{id}/
Authorization: Bearer <token>
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request data",
  "details": { "field": ["Error message"] }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "error": "权限不足"
}
```

### 404 Not Found
```json
{
  "error": "资源不存在"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error message"
}
```

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting in production.

## Pagination

List endpoints support pagination:
```json
{
  "count": 100,
  "next": "http://api.example.com/measurements/?page=2",
  "previous": null,
  "results": [...]
}
```

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (localStorage or secure cookies)
3. **Refresh tokens before expiration** (access tokens expire in 1 hour)
4. **Handle errors gracefully** in the frontend
5. **Validate data on client side** before sending to API
6. **Use appropriate HTTP methods** (GET for reading, POST for creating, PUT for updating, DELETE for deleting)
7. **Include meaningful error messages** for better user experience
