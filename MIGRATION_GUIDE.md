# Migration Guide

This guide helps you migrate from the previous version to the new enhanced health management system.

## Overview of Changes

### New Features
1. **Multi-dimensional Health Scoring**: 6-dimension health evaluation with radar chart
2. **Health Forecasting**: Predictive analytics for health metrics
3. **Extended Tracking**: Medication, sleep, and mood logging
4. **Enhanced Profile**: Age, gender, blood type, height, weight baseline
5. **Avatar Support**: User profile pictures
6. **Improved Navigation**: Sidebar navigation and header bar
7. **Password Management**: Change password functionality

### Database Changes

New tables added:
- `MedicationRecord`: Track medications
- `SleepLog`: Track sleep patterns
- `MoodLog`: Track daily mood

Extended tables:
- `User`: Added `avatar` field
- `Profile`: Added `age`, `gender`, `blood_type`, `height_cm`, `weight_baseline_kg`

## Migration Steps

### 1. Backup Your Data

Before migrating, backup your existing database:

```bash
# For SQLite
cp backend/db.sqlite3 backend/db.sqlite3.backup

# For PostgreSQL
pg_dump your_database > backup.sql
```

### 2. Update Code

Pull the latest changes:

```bash
git pull origin main
```

### 3. Backend Migration

#### Install New Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies:
- `Pillow==10.1.0` - Image processing for avatars
- `statsmodels==0.14.1` - Time series forecasting
- `pandas==2.1.4` - Data processing

#### Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Create Media Directory

```bash
mkdir -p media/avatars
```

#### Update Settings (if needed)

Ensure your `settings.py` includes:

```python
# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# In INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'users',
    'measurements',
]
```

### 4. Frontend Migration

#### Install New Dependencies

```bash
cd frontend
npm install
```

No new dependencies - all are already in package.json.

#### Update Environment Variables

Create or update `.env.local`:

```env
VITE_API_BASE_URL=/api
VITE_BACKEND_URL=http://localhost:8000
```

#### Build and Test

```bash
npm run build
npm run dev
```

### 5. Data Migration

#### Populate Extended Profile Fields

Existing users will have `NULL` values for new profile fields. They should be prompted to complete their profile:

1. Age
2. Gender
3. Blood type
4. Height
5. Weight baseline

This can be done through the new "个人基本档案" (Personal Profile) page.

#### Optional: Seed Demo Data

If you want demo data for the new features:

```bash
cd backend
python manage.py shell
```

```python
from users.models import User, Profile, MedicationRecord, SleepLog, MoodLog
from datetime import date, datetime, timedelta

# Get a test user
user = User.objects.first()

# Create medication record
MedicationRecord.objects.create(
    user=user,
    medication_name="Vitamin D",
    dosage="1000 IU",
    frequency="每日1次",
    start_date=date.today() - timedelta(days=30),
    notes="早餐后服用"
)

# Create sleep log
SleepLog.objects.create(
    user=user,
    sleep_date=date.today(),
    start_time=datetime.now() - timedelta(hours=8),
    end_time=datetime.now(),
    duration_minutes=480,
    quality_rating=8
)

# Create mood log
MoodLog.objects.create(
    user=user,
    log_date=date.today(),
    mood_rating=7,
    notes="Feeling good"
)
```

### 6. API Endpoint Changes

#### Deprecated Endpoints
None - all existing endpoints remain functional.

#### New Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/change-password/` | Change user password |
| `GET/PUT /api/profile/me/` | Get/update profile |
| `GET /api/health-report/` | Generate health report with scoring |
| `GET /api/forecast/` | Forecast health metrics |
| `GET/POST /api/medications/` | Medication CRUD |
| `GET/POST /api/sleep-logs/` | Sleep log CRUD |
| `GET/POST /api/mood-logs/` | Mood log CRUD |

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for full details.

### 7. Frontend Route Changes

#### New Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/personal-center` | PersonalCenter | User account management |
| `/profile` | PersonalProfile | Basic health profile |
| `/measurements` | MeasurementsEnhanced | Enhanced measurements with prediction |
| `/medications` | MedicationLogs | Medication tracking |
| `/sleep-logs` | SleepLogs | Sleep tracking |
| `/mood-logs` | MoodLogs | Mood tracking |
| `/health-report` | HealthReportNew | New health report with scoring |

#### Updated Components

- **Dashboard**: Now includes sidebar navigation
- **Health Report**: Enhanced with radar chart and scoring
- **Measurements**: Added prediction overlay

### 8. Configuration Updates

#### Backend Configuration

Update `backend/health_management_system/settings.py`:

```python
# Ensure these settings are present
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# In urls.py, add media serving in development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

#### Frontend Configuration

No changes required - existing configuration works.

### 9. Testing the Migration

#### Test Checklist

- [ ] Login with existing account
- [ ] View existing health records
- [ ] Add a new measurement
- [ ] View health report (old and new versions)
- [ ] Complete personal profile
- [ ] Upload avatar
- [ ] Change password
- [ ] Add medication log
- [ ] Add sleep log
- [ ] Add mood log
- [ ] View prediction on measurements page

#### Automated Tests

Run backend tests:
```bash
cd backend
pytest
```

Build frontend:
```bash
cd frontend
npm run build
```

### 10. Rollback Plan

If you encounter issues:

1. **Restore database backup**:
   ```bash
   cp backend/db.sqlite3.backup backend/db.sqlite3
   ```

2. **Revert to previous git commit**:
   ```bash
   git log  # Find previous commit hash
   git checkout <previous-commit-hash>
   ```

3. **Reinstall dependencies**:
   ```bash
   cd backend && pip install -r requirements.txt
   cd ../frontend && npm install
   ```

## Common Issues and Solutions

### Issue 1: Migration Fails

**Error**: `django.db.utils.OperationalError: no such table`

**Solution**: 
```bash
python manage.py migrate --run-syncdb
```

### Issue 2: Avatar Upload Fails

**Error**: `IOError: cannot write mode RGBA as JPEG`

**Solution**: Ensure Pillow is installed and media directory exists:
```bash
pip install Pillow
mkdir -p media/avatars
```

### Issue 3: Forecasting Error

**Error**: `ValueError: Not enough data points for forecasting`

**Solution**: Forecasting requires at least 3 data points. Add more measurements before using the prediction feature.

### Issue 4: Frontend Build Warnings

**Warning**: `Some chunks are larger than 500 kBs`

**Solution**: This is normal for ECharts. Optionally, you can code-split:
```javascript
// In vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'echarts': ['echarts']
        }
      }
    }
  }
}
```

## Post-Migration Tasks

1. **Inform Users**: Send notification about new features
2. **Monitor Logs**: Check for any errors in the first few days
3. **Gather Feedback**: Ask users about the new features
4. **Update Documentation**: Update any internal docs
5. **Performance Check**: Monitor API response times

## Support

If you encounter issues not covered in this guide:

1. Check the [README.md](./README.md) for setup instructions
2. Review [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for API details
3. Check application logs:
   - Backend: Console output or Django logs
   - Frontend: Browser console (F12)
4. Open an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version, Node version)

## Feedback

We welcome feedback on the migration process. Please report:
- Missing information in this guide
- Errors encountered during migration
- Suggestions for improvement

Open an issue or pull request on GitHub.
