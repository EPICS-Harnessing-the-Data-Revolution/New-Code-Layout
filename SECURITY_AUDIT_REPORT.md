# Security Audit Report: Exposed API Keys and Secrets

**Date:** November 20, 2024  
**Repository:** EPICS-Harnessing-the-Data-Revolution/New-Code-Layout  
**Audit Type:** Exposed Credentials and API Keys Search

---

## Executive Summary

This security audit identified **4 critical security vulnerabilities** involving exposed API keys, credentials, and secrets hardcoded in the repository. These exposed credentials pose significant security risks including unauthorized access, data breaches, and service abuse.

**Severity:** HIGH  
**Risk Level:** CRITICAL

---

## Detailed Findings

### 1. NOAA API Key Exposure
**Severity:** HIGH  
**File:** `services/backend/datasources/noaa_source.py`  
**Line:** 69  
**Type:** Hardcoded API Key

```python
self.api_token = os.getenv(
    "NOAA_API_TOKEN", "WkaDdDnFDuEUpiUEFiNMFcLcNKVsQgtp"
)
```

**Risk:**
- Exposed NOAA API token can be used by unauthorized parties
- API rate limits may be exhausted by malicious actors
- Account may be suspended or blocked by NOAA
- Historical data in git history maintains this exposure

**Recommendation:**
1. Immediately revoke the exposed API token at https://www.ncdc.noaa.gov/cdo-web/token
2. Generate a new API token
3. Remove the hardcoded fallback value
4. Use empty string or None as fallback: `os.getenv("NOAA_API_TOKEN", None)`
5. Document in README that users must set the NOAA_API_TOKEN environment variable

---

### 2. Mapbox Access Token Exposure
**Severity:** MEDIUM-HIGH  
**File:** `static/js/map.js`  
**Line:** 1  
**Type:** Public Access Token

```javascript
mapboxgl.accessToken = 'pk.eyJ1IjoiYWxleGlzMTMiLCJhIjoiY2xkeGk4bXpvMDJmeTNwbXV2bmpleGxxeCJ9.4PMbriYdSiVtIskoEwAsfw';
```

**Risk:**
- Exposed Mapbox token can be used by third parties
- May incur unexpected charges if usage exceeds free tier
- Token cannot be easily rotated without updating client code
- Token is visible in browser developer tools (inherent to client-side apps)

**Note:** Mapbox public tokens (starting with `pk.`) are designed to be used client-side and are less sensitive than secret tokens. However, they should still be protected with URL restrictions.

**Recommendation:**
1. Configure URL restrictions in Mapbox dashboard to limit token usage to specific domains
2. Monitor token usage in Mapbox dashboard for abnormal patterns
3. Consider using environment variables during build process for different environments
4. Rotate token if unauthorized usage is detected

---

### 3. Email Credentials Exposure
**Severity:** CRITICAL  
**File:** `config/info.py`  
**Lines:** 1-5  
**Type:** Plaintext Email Password

```python
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER= '123testing.matteo@gmail.com'
EMAIL_HOST_PASSWORD= 'Lucas2009'
EMAIL_PORT = 587
```

**Risk:**
- Full access to the email account `123testing.matteo@gmail.com`
- Potential for account compromise and unauthorized access
- Risk of spam/phishing campaigns sent from compromised account
- Possible access to other services using same credentials
- Gmail may flag account for suspicious activity

**Recommendation:**
1. **IMMEDIATE ACTION:** Change the password for `123testing.matteo@gmail.com`
2. Review account activity for unauthorized access
3. Enable 2-factor authentication on the Gmail account
4. Use Gmail App Password instead of account password
5. Move credentials to environment variables
6. Add `config/info.py` to `.gitignore`
7. Create `config/info.py.example` as a template without real credentials
8. Consider using a dedicated service email or transactional email service (SendGrid, AWS SES, etc.)

---

### 4. Django Secret Key Exposure
**Severity:** CRITICAL  
**File:** `config/settings.py`  
**Line:** 29  
**Type:** Hardcoded Secret Key

```python
SECRET_KEY = 'django-insecure-+9wcfz&b8$a30aq(9-$s&a^*#6lsvy^jb@3as4$0%c@f=g!cvb'
```

**Risk:**
- Django SECRET_KEY is used for cryptographic signing
- Compromise allows session hijacking and CSRF token forgery
- Can decrypt password reset tokens and session data
- Enables potential remote code execution through pickle deserialization attacks
- The 'django-insecure' prefix indicates it's a development key

**Recommendation:**
1. Generate a new SECRET_KEY using: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
2. Store SECRET_KEY in environment variable
3. Update settings.py to: `SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')`
4. Never commit the real SECRET_KEY to version control
5. Use different SECRET_KEYs for different environments (dev, staging, production)
6. If this application is in production, rotate all session tokens and passwords

---

## Additional Findings

### File: `config/api_config.py`
This file contains placeholder text for tokens, which is good practice:
```python
NOAA_API_TOKEN = os.getenv("NOAA_API_TOKEN", "YOUR_NOAA_TOKEN_HERE")
```

However, users might accidentally commit real tokens when replacing placeholders.

---

## Git History Considerations

**IMPORTANT:** The exposed secrets have been committed to git history. Simply removing them from current files is insufficient because they remain accessible in git history.

### To completely remove secrets from git history:

1. **Option 1: BFG Repo-Cleaner (Recommended)**
```bash
# Install BFG
# Replace exposed secrets
bfg --replace-text secrets.txt repo.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

2. **Option 2: git-filter-repo**
```bash
git filter-repo --replace-text secrets.txt
git push --force
```

3. **Option 3: GitHub Secret Scanning**
Contact GitHub support to remove exposed secrets from cache

**Warning:** Force pushing rewrites history and affects all collaborators. Coordinate with team before executing.

---

## Remediation Priority

1. **IMMEDIATE (Within 24 hours):**
   - Change Gmail password
   - Revoke and rotate NOAA API key
   - Generate and set new Django SECRET_KEY
   - Add `config/info.py` to `.gitignore`

2. **HIGH (Within 1 week):**
   - Configure Mapbox token URL restrictions
   - Remove hardcoded secrets from code
   - Implement environment variable usage
   - Create `.env.example` template file

3. **MEDIUM (Within 2 weeks):**
   - Update deployment documentation with environment variable setup
   - Implement secrets scanning in CI/CD pipeline
   - Consider using secrets management service (AWS Secrets Manager, Azure Key Vault, etc.)

4. **LOW (Within 1 month):**
   - Clean git history of exposed secrets
   - Implement pre-commit hooks to prevent secret commits
   - Security training for team members

---

## Best Practices for Future Development

### 1. Use Environment Variables
Never hardcode secrets in source code. Use environment variables:

```python
# Good
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

# Bad
API_KEY = "actual-secret-key-here"
```

### 2. Use .env Files (Not Committed)
```bash
# .env (in .gitignore)
NOAA_API_TOKEN=your_token_here
DJANGO_SECRET_KEY=your_secret_key_here

# .env.example (committed)
NOAA_API_TOKEN=your_noaa_token_here
DJANGO_SECRET_KEY=your_django_secret_key_here
```

### 3. Configure .gitignore
```
# .gitignore
.env
.env.local
.env.*.local
config/info.py
secrets.json
*.key
*.pem
```

### 4. Use Pre-commit Hooks
Install tools like:
- `detect-secrets`
- `git-secrets`
- `truffleHog`
- `gitleaks`

### 5. Implement CI/CD Secret Scanning
Add secret scanning to GitHub Actions or other CI/CD:
```yaml
- name: Secret Scan
  uses: trufflesecurity/trufflehog@main
```

### 6. Use Secrets Management Services
For production:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Google Secret Manager
- Doppler
- 1Password Secrets Automation

---

## Environment Variable Configuration Guide

### Development Setup

1. Create `.env` file in project root:
```bash
# NOAA API Configuration
NOAA_API_TOKEN=your_noaa_token_here

# Django Configuration
DJANGO_SECRET_KEY=your_generated_secret_key_here

# Email Configuration (use App Password for Gmail)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password_here
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

2. Load environment variables:
```python
# Using python-dotenv
from dotenv import load_dotenv
load_dotenv()

# Or using django-environ
import environ
env = environ.Env()
environ.Env.read_env()
```

### Production Deployment

For Azure App Service:
```bash
az webapp config appsettings set --name <app-name> --resource-group <group> \
  --settings NOAA_API_TOKEN="<token>" DJANGO_SECRET_KEY="<key>"
```

---

## Compliance and Regulations

Organizations should be aware of:
- **GDPR**: Data protection requirements
- **PCI-DSS**: If handling payment information
- **SOC 2**: Trust service criteria
- **HIPAA**: If handling health information

Exposed credentials may violate compliance requirements.

---

## References

- [OWASP Top 10 - A02:2021 Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)
- [Django Security Settings](https://docs.djangoproject.com/en/stable/topics/security/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [NIST Guidelines on Application Security](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)

---

## Conclusion

This audit identified critical security vulnerabilities that require immediate attention. The exposed credentials in this repository present significant risks to the application's security and should be addressed following the priority timeline outlined above.

**Next Steps:**
1. Review this report with the development team
2. Execute immediate remediation actions
3. Implement preventive measures
4. Schedule regular security audits

For questions or clarifications, please contact the security team.

---

**Report Generated:** November 20, 2024  
**Auditor:** Automated Security Scan  
**Classification:** CONFIDENTIAL
