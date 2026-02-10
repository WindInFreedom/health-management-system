# Health Management System (健康管理系统)

A comprehensive web-based health management system built with Vue.js (frontend) and Django REST Framework (backend). This system provides users with tools to track health metrics, visualize trends, receive personalized health reports with scoring, and forecast future health indicators.

## 🌟 Features

### User Features
- **Personal Dashboard**: Overview of health status with key metrics
- **Health Records Management**: Track weight, blood pressure, heart rate, blood glucose
- **Predictive Analytics**: Forecast health metrics using time series analysis
- **Comprehensive Health Report**: 
  - Multi-dimensional health scoring (0-100 scale)
  - Radar chart visualization of 6 key health dimensions
  - Personalized suggestions based on scores
- **Extended Tracking**:
  - Medication logs (dosage, frequency, dates)
  - Sleep tracking (duration, quality rating, trends)
  - Mood index (daily ratings with trend analysis)
- **Personal Profile**: Age, gender, blood type, height, weight baseline
- **Avatar & Account Management**: Upload avatar, change password

### Admin/Doctor Features
- User management
- Health statistics overview
- Access to all user health data
- Health alerts and warnings

### Technical Features
- JWT-based authentication
- RESTful API architecture
- Responsive design (mobile & desktop)
- Real-time data visualization with ECharts
- Time series forecasting (ARIMA/ETS)
- Configurable health scoring with clinical ranges

## 🏗️ Architecture

### Frontend
- **Framework**: Vue 3 (Composition API)
- **UI Library**: Element Plus
- **Charts**: ECharts 5.6
- **State Management**: Pinia
- **Routing**: Vue Router 4
- **Build Tool**: Vite 4

### Backend
- **Framework**: Django 4.2 with Django REST Framework
- **Authentication**: JWT (Simple JWT)
- **Database**: SQLite (development), PostgreSQL-ready
- **Analytics**: statsmodels, pandas, numpy, scipy
- **Image Processing**: Pillow

## 📦 Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Git

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/WindInFreedom/health-management-system.git
cd health-management-system/backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser (optional):
```bash
python manage.py createsuperuser
```

6. Start development server:
```bash
python manage.py runserver
```

The backend API will be available at `http://localhost:8000/api/`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd ../frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment configuration:
```bash
cp .env.example .env.local
```

4. Edit `.env.local` and set your backend URL:
```env
VITE_API_BASE_URL=/api
VITE_BACKEND_URL=http://localhost:8000
```

5. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173/`

## 🔑 Environment Variables

### Backend (Optional)
Create a `.env` file in `backend/` directory:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend
Create a `.env.local` file in `frontend/` directory:
```env
# API configuration
VITE_API_BASE_URL=/api
VITE_BACKEND_URL=http://localhost:8000
```

## 📚 API Documentation

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/change-password/` - Change password

### User Management
- `GET /api/users/me/` - Get current user info
- `GET /api/profile/me/` - Get/update user profile

### Health Records
- `GET /api/measurements/` - List measurements
- `POST /api/measurements/` - Create measurement
- `PUT /api/measurements/{id}/` - Update measurement
- `DELETE /api/measurements/{id}/` - Delete measurement

### Health Reporting & Analytics
- `GET /api/health-report/?days=30` - Generate comprehensive health report with scoring
- `GET /api/forecast/?metric=systolic&horizon=30` - Forecast health metric

### Extended Tracking
- `GET /api/medications/` - List medication records
- `POST /api/medications/` - Create medication record
- `GET /api/sleep-logs/` - List sleep logs
- `POST /api/sleep-logs/` - Create sleep log
- `GET /api/mood-logs/` - List mood logs
- `POST /api/mood-logs/` - Create mood log

### Health Scoring Dimensions
The health report evaluates 6 key dimensions:
1. **BMI Index** (20% weight)
2. **Blood Pressure** (25% weight)
3. **Heart Rate** (15% weight)
4. **Blood Glucose** (20% weight)
5. **Sleep Quality** (10% weight)
6. **Mood Index** (10% weight)

Each dimension is scored 0-100 based on clinical ranges and optimal values.

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Build Test
```bash
cd frontend
npm run build
```

## 🚀 Deployment

### Production Build

#### Backend
```bash
cd backend
# Update settings for production
python manage.py collectstatic
gunicorn health_management_system.wsgi:application
```

#### Frontend
```bash
cd frontend
npm run build
# Deploy dist/ folder to web server
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend Framework | Vue 3 |
| UI Components | Element Plus |
| Charts | ECharts |
| State Management | Pinia |
| HTTP Client | Axios |
| Backend Framework | Django 4.2 |
| API Framework | Django REST Framework |
| Authentication | JWT (djangorestframework-simplejwt) |
| Database | SQLite / PostgreSQL |
| Time Series Analysis | statsmodels |
| Data Processing | pandas, numpy |

## 📖 User Guide

### Getting Started
1. Register a new account or login
2. Complete your personal profile (age, gender, blood type, height, weight)
3. Start recording health measurements
4. View your health report after accumulating data (recommended: at least 5-10 measurements)

### Understanding Your Health Report
- **Scores**: 80-100 (Excellent), 60-79 (Good), <60 (Needs Attention)
- **Radar Chart**: Visualizes your health across 6 dimensions
- **Suggestions**: Personalized recommendations based on your scores

### Using Predictions
- Select a health metric (e.g., blood pressure)
- Enable "Show Prediction" toggle
- Choose forecast horizon (7, 14, or 30 days)
- View predicted trends with confidence intervals

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- WindInFreedom - Initial work

## 🙏 Acknowledgments

- Element Plus for the UI components
- ECharts for visualization
- Django REST Framework for the API
- statsmodels for forecasting capabilities

## 📞 Support

For issues and questions, please open an issue on GitHub.
