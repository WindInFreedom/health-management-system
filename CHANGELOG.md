# Changelog

All notable changes to the Health Management System will be documented in this file.

## [2.0.0] - 2024-02-04

### Added - Backend

#### Core Features
- **Health Scoring Service** (`measurements/health_scoring.py`)
  - Multi-dimensional health evaluation across 6 dimensions
  - Configurable scoring with clinical ranges
  - Personalized suggestions based on scores
  - Dimensions: BMI, Blood Pressure, Heart Rate, Blood Glucose, Sleep Quality, Mood Index

- **Forecasting Service** (`measurements/forecasting.py`)
  - Time series forecasting using ARIMA/ETS/Linear Regression
  - Support for 5 metrics: systolic, diastolic, heart_rate, blood_glucose, weight_kg
  - Confidence intervals for predictions
  - Adaptive model selection based on data availability
  - Graceful fallback for limited data

#### New Models
- **MedicationRecord**: Track user medications with dosage, frequency, dates
- **SleepLog**: Track sleep patterns with auto-calculated duration
- **MoodLog**: Track daily mood ratings (1-10 scale)
- **Extended User Model**: Added `avatar` field for profile pictures
- **Extended Profile Model**: Added age, gender, blood_type, height_cm, weight_baseline_kg

#### New API Endpoints
- `GET /api/health-report/` - Generate comprehensive health report
- `GET /api/health-report/{user_id}/` - Get report for specific user (admin/doctor)
- `GET /api/forecast/` - Forecast health metrics
- `POST /api/auth/change-password/` - Change user password
- `GET/PUT /api/profile/me/` - Manage user profile
- Full CRUD for `/api/medications/`, `/api/sleep-logs/`, `/api/mood-logs/`

#### Dependencies
- Added `Pillow==10.1.0` for image processing
- Added `statsmodels==0.14.1` for time series analysis
- Added `pandas==2.1.4` for data manipulation

#### Configuration
- Created `health_management_system/settings.py` with full Django configuration
- Created `health_management_system/urls.py` with API routing
- Added media file handling for avatar uploads
- Configured CORS for frontend integration

### Added - Frontend

#### New Components
- **Sidebar.vue**: Collapsible navigation sidebar with gradient design
- **HeaderBar.vue**: Top header with user avatar and dropdown menu
- **DashboardLayout.vue**: Layout wrapper with sidebar and header

#### New Pages
- **PersonalCenter.vue**: User account management (username, password, avatar)
- **PersonalProfile.vue**: Basic health profile with demographic information
- **HealthReportNew.vue**: Enhanced health report with radar chart and scoring
- **MeasurementsEnhanced.vue**: Measurements with prediction overlay
- **MedicationLogs.vue**: Medication tracking with table view
- **SleepLogs.vue**: Sleep tracking with duration chart
- **MoodLogs.vue**: Mood tracking with trend visualization

#### Enhanced Features
- **Predictive Analytics**: Overlay predicted trends on measurement charts
- **Health Scoring**: Radar chart visualization of 6 health dimensions
- **Navigation**: Unified sidebar navigation across all user pages
- **User Experience**: Avatar support, profile editing, password change

#### Routing Updates
- Implemented nested routes with DashboardLayout
- Added routes for all new pages
- Maintained backward compatibility with existing routes

### Changed

#### Backend
- Updated `users/models.py` to include new fields and tracking models
- Enhanced `users/serializers.py` with serializers for new models
- Extended `users/views.py` with viewsets for medication, sleep, mood tracking
- Updated `users/urls.py` to include new endpoints
- Enhanced `measurements/views.py` with health report and forecasting endpoints
- Updated `measurements/urls.py` to include new analytics endpoints

#### Frontend
- Restructured router to use layout with nested routes
- Enhanced user dashboard with sidebar navigation
- Updated authentication store for avatar handling
- Improved responsive design for mobile devices

### Security
- All new endpoints require authentication (JWT)
- Password change requires old password verification
- Passwords are hashed using Django's default hasher (PBKDF2)
- Profile updates restricted to own user only
- Input validation on all forms
- CodeQL security scan: 0 vulnerabilities found

### Documentation
- Created comprehensive `README.md` with installation and usage instructions
- Added `API_DOCUMENTATION.md` with full API reference
- Added `MIGRATION_GUIDE.md` for upgrading from previous versions
- Created `CHANGELOG.md` to track all changes
- Inline code comments throughout new modules

### Technical Improvements
- Modular architecture for scoring and forecasting services
- RESTful API design with proper HTTP methods
- Responsive UI with mobile-first approach
- Error handling with meaningful messages
- Loading states for better UX
- Configurable parameters (evaluation periods, forecast horizons)

### Performance
- Efficient database queries with select_related/prefetch_related
- Lazy loading of prediction data
- Chart rendering optimization with ECharts
- Responsive chart resize handling

### Testing
- Frontend build test: Passed
- Backend Django check: 0 issues
- Security scan (CodeQL): 0 alerts
- API endpoint functionality: Manually verified

## [1.0.0] - Previous Version

### Features
- Basic health measurement tracking
- User authentication with JWT
- Simple health statistics
- Basic visualization with charts
- Doctor and admin dashboards
- Collaborative filtering for recommendations

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## Migration Notes

For upgrading from 1.0.0 to 2.0.0, see [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md).

## Upcoming Features

See GitHub Issues for planned features and enhancements.
