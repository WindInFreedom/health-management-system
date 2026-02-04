# Health Management System (健康管理系统)

A comprehensive health management system built with Django backend and Vue.js frontend, featuring multi-dimensional health reporting, predictive analytics, real-time admin dashboard, and extended health tracking capabilities.

## 🎯 Features

### Implemented Features ✅

#### Backend (Django)
1. **Extended Health Data Models**
   - User profile with avatar support (avatarUrl field)
   - Enhanced Profile model (age, gender, blood type, height, weight baseline)
   - Medication records (name, dosage, frequency, dates, notes)
   - Sleep logs with auto-calculated duration
   - Mood logs with rating (1-10)

2. **Health Scoring Service**
   - Multi-dimensional health scoring algorithm
   - BMI, blood pressure, heart rate, blood glucose scoring
   - Sleep quality and mood index scoring
   - Configurable weights per metric
   - Rule-based health advice generation

3. **Health Report API**
   - GET /api/measurements/health-report/ - Current user report
   - GET /api/measurements/health-report/{user_id}/ - Specific user report
   - Returns dimensions with scores and advice
   - Overall health score calculation

4. **Health Forecast API**
   - GET /api/measurements/health-forecast/ - Predictive analytics
   - Moving average-based predictions
   - Confidence intervals
   - Trend analysis (increasing/decreasing/stable)

5. **Extended Health Data APIs**
   - /api/measurements/medications/ - CRUD for medication records
   - /api/measurements/sleep-logs/ - CRUD for sleep logs with statistics
   - /api/measurements/mood-logs/ - CRUD for mood logs with trends
   - /api/auth/profiles-extended/ - Extended profile management

6. **User Management**
   - /api/auth/user-profile/me/ - Get/Update user profile
   - /api/auth/change-password/ - Password change endpoint
   - /api/auth/upload-avatar/ - Avatar upload (S3 or local storage)
   - Username uniqueness validation

7. **Real-time Admin Dashboard (WebSocket)**
   - ws://localhost:8000/ws/admin/stream/ - Real-time data streaming
   - System statistics (active users, measurements, averages)
   - Health alerts detection (high BP, glucose, abnormal HR)
   - Periodic updates every 5 seconds

#### Frontend (Vue.js)
1. **Layout Components**
   - Sidebar.vue - Left navigation sidebar with menu items
   - HeaderBar.vue - Top header with avatar dropdown and notifications
   - Responsive design for mobile and desktop

2. **Existing Pages**
   - Login/Register pages
   - Dashboard views (User, Doctor, Admin)
   - Measurements list and visualization
   - Simple health report

### Planned Features (Not Yet Implemented) 📋

#### Frontend Components
1. **Personal Center Page**
   - Edit username and password
   - Upload and preview avatar
   - Profile information display

2. **Enhanced Health Report with Radar Chart**
   - ECharts radar chart visualization
   - Multi-dimensional score display
   - Dimension cards with detailed advice
   - Export functionality (image/PDF)

3. **Extended Health Data UIs**
   - MedicationLogs.vue - Medication CRUD interface
   - SleepLogs.vue - Sleep tracking with duration charts
   - MoodLogs.vue - Mood tracking with trend visualization
   - Profile edit form

4. **Visualization with Predictions**
   - Forecast toggle controls
   - Prediction overlay on charts
   - Confidence bands display

5. **Real-time Admin Dashboard UI**
   - WebSocket connection setup
   - Live charts (gauges, line charts, heatmaps)
   - Real-time metrics display
   - Animated updates

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 4.2.7
- **REST API**: Django REST Framework 3.14.0
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: SQLite (dev) / MySQL (production)
- **WebSocket**: Django Channels 4.0.0
- **Object Storage**: boto3 (S3-compatible)
- **Analytics**: numpy, scipy, pandas, statsmodels, scikit-learn
- **Password Hashing**: argon2-cffi

### Frontend
- **Framework**: Vue 3.4.0
- **UI Library**: Element Plus 2.13.1
- **Charts**: ECharts 5.6.0
- **HTTP Client**: Axios 1.4.0
- **State Management**: Pinia 2.0.0
- **Routing**: Vue Router 4.6.4
- **Build Tool**: Vite 4.5.0

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- MySQL 8.0+ (optional, for production)
- Redis (optional, for Channels in production)

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/WindInFreedom/health-management-system.git
cd health-management-system/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

Key environment variables:
```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (set USE_MYSQL=True for MySQL)
USE_MYSQL=False
MYSQL_DATABASE=health_management
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_HOST=localhost
MYSQL_PORT=3306

# S3 Storage (set USE_S3_STORAGE=True to enable)
USE_S3_STORAGE=False
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=health-management
AWS_S3_ENDPOINT_URL=https://s3.amazonaws.com
```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Load demo data (optional)**
```bash
python manage.py loaddata fixtures/demo_users_fixed.json
python manage.py loaddata fixtures/demo_measurements.json
```

8. **Run development server**
```bash
# HTTP server
python manage.py runserver

# ASGI server (for WebSocket support)
daphne -p 8000 health_management_system.asgi:application
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd ../frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure API endpoint**
Edit `src/utils/axios.js` if needed to point to your backend URL.

4. **Run development server**
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `GET /api/auth/users/me/` - Get current user info
- `PUT /api/auth/user-profile/me/` - Update user profile
- `POST /api/auth/change-password/` - Change password
- `POST /api/auth/upload-avatar/` - Upload avatar

### Health Measurements
- `GET /api/measurements/measurements/` - List measurements
- `POST /api/measurements/measurements/` - Create measurement
- `GET /api/measurements/measurements/{id}/` - Get measurement
- `PUT /api/measurements/measurements/{id}/` - Update measurement
- `DELETE /api/measurements/measurements/{id}/` - Delete measurement
- `GET /api/measurements/measurements/statistics/` - Get statistics
- `GET /api/measurements/measurements/predict/` - Get predictions

### Health Reports
- `GET /api/measurements/health-report/` - Get current user health report
- `GET /api/measurements/health-report/{user_id}/` - Get specific user report
- `GET /api/measurements/health-forecast/` - Get health forecast
- `GET /api/measurements/health-forecast/{user_id}/` - Get user forecast

### Extended Health Data
- `GET/POST /api/measurements/medications/` - Medication records
- `GET/PUT/DELETE /api/measurements/medications/{id}/` - Medication detail
- `GET/POST /api/measurements/sleep-logs/` - Sleep logs
- `GET /api/measurements/sleep-logs/statistics/` - Sleep statistics
- `GET/POST /api/measurements/mood-logs/` - Mood logs
- `GET /api/measurements/mood-logs/statistics/` - Mood statistics

### Profiles
- `GET/PUT /api/auth/profiles-extended/me/` - Current user profile
- `GET /api/auth/profiles-extended/{id}/` - Specific profile

### Admin (WebSocket)
- `ws://localhost:8000/ws/admin/stream/` - Real-time admin data stream

## 🔐 Security Features

1. **Authentication**: JWT-based authentication
2. **Password Hashing**: Argon2 password hashing
3. **Input Validation**: Comprehensive validation on all endpoints
4. **Permission Checks**: Role-based access control
5. **CORS Configuration**: Configurable allowed origins
6. **File Upload Validation**: Type and size checks for avatar uploads

## 🏗️ Project Structure

```
health-management-system/
├── backend/
│   ├── health_management_system/
│   │   ├── settings.py          # Django settings
│   │   ├── urls.py              # URL routing
│   │   ├── wsgi.py              # WSGI config
│   │   └── asgi.py              # ASGI config (Channels)
│   ├── users/
│   │   ├── models.py            # User and Profile models
│   │   ├── serializers.py       # User serializers
│   │   ├── views.py             # Auth views
│   │   ├── profile_views.py     # Profile management views
│   │   └── urls.py              # User URLs
│   ├── measurements/
│   │   ├── models.py            # Health data models
│   │   ├── serializers.py       # Health data serializers
│   │   ├── views.py             # Measurement views
│   │   ├── health_views.py      # Health report views
│   │   ├── consumers.py         # WebSocket consumers
│   │   ├── routing.py           # WebSocket routing
│   │   ├── services/
│   │   │   └── scoring_service.py  # Health scoring logic
│   │   └── urls.py              # Measurement URLs
│   └── requirements.txt         # Python dependencies
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Sidebar.vue      # Left navigation sidebar
    │   │   └── HeaderBar.vue    # Top header bar
    │   ├── views/               # Page components
    │   ├── stores/              # Pinia stores
    │   ├── router/              # Vue Router config
    │   └── utils/               # Utility functions
    └── package.json             # Node dependencies
```

## 📊 Health Scoring Algorithm

The system uses a multi-dimensional scoring algorithm:

1. **Normalization**: Each metric is normalized to a 0-100 score based on clinical ranges
2. **Weighting**: Configurable weights per dimension:
   - Blood Pressure: 25%
   - Blood Glucose: 20%
   - BMI: 15%
   - Heart Rate: 15%
   - Cholesterol: 10%
   - Activity: 5%
   - Sleep Quality: 5%
   - Mood: 5%
3. **Advice Generation**: Rule-based advice for each dimension and overall health

## 🔄 Real-time Features

The admin dashboard uses WebSocket (Django Channels) to provide:
- Live system statistics updates every 5 seconds
- Real-time health alert notifications
- Active user monitoring
- Average health metrics tracking

## 🚀 Deployment

### Production Checklist
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Generate secure `DJANGO_SECRET_KEY`
- [ ] Configure MySQL database
- [ ] Set up Redis for Channels
- [ ] Configure S3 for avatar storage
- [ ] Set up proper CORS origins
- [ ] Configure Nginx/Apache reverse proxy
- [ ] Enable HTTPS
- [ ] Set up monitoring and logging

### Recommended Stack
- **Web Server**: Nginx
- **WSGI Server**: Gunicorn
- **ASGI Server**: Daphne
- **Database**: MySQL 8.0+
- **Cache/Channels**: Redis
- **Storage**: AWS S3 or compatible

## 🧪 Testing

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm run test
```

## 📝 License

This project is for educational and demonstration purposes.

## 👥 Contributors

- WindInFreedom - Initial work

## 🙏 Acknowledgments

- Django REST Framework
- Vue.js and Element Plus
- ECharts for data visualization
- Django Channels for WebSocket support
