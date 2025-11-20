# IMMEDIATE ACTION REQUIRED - Security Incident Response

**Date:** November 20, 2024  
**Priority:** CRITICAL  
**Estimated Time:** 30-60 minutes

---

## 🚨 CRITICAL ACTIONS (Complete within 24 hours)

### 1. Gmail Account Security ⏰ 15 minutes
**Email:** `123testing.matteo@gmail.com`  
**Status:** ⬜ Not Started

Steps:
- [ ] Change password immediately at https://myaccount.google.com/security
- [ ] Review account activity: https://myaccount.google.com/notifications
- [ ] Enable 2-Factor Authentication
- [ ] Generate App Password: https://myaccount.google.com/apppasswords
- [ ] Update `.env` with App Password (not account password)
- [ ] Review "Less secure app access" settings (should be OFF)
- [ ] Check for unauthorized email forwarding rules

**Verification:**
```bash
# Test new credentials
python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587)"
```

---

### 2. NOAA API Token ⏰ 10 minutes
**Current Token:** `WkaDdDnFDuEUpiUEFiNMFcLcNKVsQgtp`  
**Status:** ⬜ Not Started

Steps:
- [ ] Visit https://www.ncdc.noaa.gov/cdo-web/token
- [ ] Request token revocation (if possible)
- [ ] Generate new token with your email
- [ ] Verify new token in email
- [ ] Add to `.env`: `NOAA_API_TOKEN=new_token_here`
- [ ] Remove hardcoded token from `services/backend/datasources/noaa_source.py`
- [ ] Test new token with API call

**Code change needed:**
```python
# In services/backend/datasources/noaa_source.py line 68-70
# CHANGE FROM:
self.api_token = os.getenv(
    "NOAA_API_TOKEN", "WkaDdDnFDuEUpiUEFiNMFcLcNKVsQgtp"
)

# CHANGE TO:
self.api_token = os.getenv("NOAA_API_TOKEN")
if not self.api_token:
    raise ValueError("NOAA_API_TOKEN environment variable not set")
```

---

### 3. Django Secret Key ⏰ 10 minutes
**Current Key:** `django-insecure-+9wcfz&b8$a30aq(9-$s&a^*#6lsvy^jb@3as4$0%c@f=g!cvb`  
**Status:** ⬜ Not Started

Steps:
- [ ] Generate new secret key:
  ```bash
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  ```
- [ ] Add to `.env`: `DJANGO_SECRET_KEY=new_key_here`
- [ ] Update `config/settings.py` to use environment variable
- [ ] If in production: rotate all user sessions
- [ ] Restart application with new key

**Code change needed:**
```python
# In config/settings.py line 29
# CHANGE FROM:
SECRET_KEY = 'django-insecure-+9wcfz&b8$a30aq(9-$s&a^*#6lsvy^jb@3as4$0%c@f=g!cvb'

# CHANGE TO:
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable not set")
```

---

### 4. Secure config/info.py ⏰ 5 minutes
**File:** `config/info.py`  
**Status:** ⬜ Not Started

Steps:
- [ ] Verify `config/info.py` is in `.gitignore` (already done)
- [ ] Create `.env` with email credentials
- [ ] Update `config/settings.py` to read from environment instead of `info.py`
- [ ] Back up `config/info.py` securely
- [ ] Delete `config/info.py` from repository
- [ ] Create `config/info.py.example` as template

**Alternative approach:**
```python
# In config/settings.py, replace line 14-23:
# REMOVE:
from . info import *

EMAIL_USE_TLS = EMAIL_USE_TLS
EMAIL_HOST = EMAIL_HOST
EMAIL_HOST_USER = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD
EMAIL_PORT = EMAIL_PORT

# ADD:
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
```

---

### 5. Mapbox Token Restrictions ⏰ 5 minutes
**Token:** `pk.eyJ1IjoiYWxleGlzMTMiLCJhIjoiY2xkeGk4bXpvMDJmeTNwbXV2bmpleGxxeCJ9.4PMbriYdSiVtIskoEwAsfw`  
**Status:** ⬜ Not Started

Steps:
- [ ] Login to https://account.mapbox.com/access-tokens/
- [ ] Find the token or create new one
- [ ] Add URL restrictions:
  - Add production domain
  - Add staging domain (if applicable)
  - Add localhost:* for development
- [ ] Set up usage alerts
- [ ] Monitor usage dashboard

**Note:** Public tokens (pk.*) are meant for client-side use, but should still be restricted.

---

## 📋 VERIFICATION CHECKLIST

After completing all actions:
- [ ] All new credentials stored in `.env` file
- [ ] `.env` file NOT committed to git
- [ ] Application starts successfully with new credentials
- [ ] Email sending works with new credentials
- [ ] NOAA API calls work with new token
- [ ] Mapbox maps display correctly
- [ ] No hardcoded secrets remain in source code
- [ ] All team members notified of changes

---

## 🔍 TESTING YOUR CHANGES

### Test Environment Variables
```bash
# Check if .env is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('NOAA:', bool(os.getenv('NOAA_API_TOKEN')))"
```

### Test Django Application
```bash
# Run Django checks
python manage.py check

# Test migrations
python manage.py migrate --check

# Start development server
python manage.py runserver
```

### Test API Connections
```bash
# Test NOAA API
python -c "from services.backend.datasources.noaa_source import NOAASource; s = NOAASource(); print('OK' if s.api_token else 'FAIL')"
```

---

## 📞 ESCALATION

If you encounter issues:
1. Do NOT commit any temporary fixes with secrets
2. Document the issue
3. Contact team lead or security team
4. Refer to `SECURITY_AUDIT_REPORT.md` for detailed guidance

---

## ⏭️ NEXT STEPS (After immediate actions)

Once critical actions are complete:
- [ ] Review `SECURITY_AUDIT_REPORT.md`
- [ ] Follow `SECURITY_SETUP.md` for proper configuration
- [ ] Update deployment environments with new secrets
- [ ] Consider git history cleanup
- [ ] Implement pre-commit hooks
- [ ] Schedule regular security audits

---

## 📝 COMPLETION SIGN-OFF

**Completed by:** ___________________  
**Date:** ___________________  
**Time:** ___________________  
**Verified by:** ___________________  

**Notes:**
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

**IMPORTANT:** Keep this checklist until all actions are completed and verified.
Do NOT delete until new credentials are confirmed working in all environments.
