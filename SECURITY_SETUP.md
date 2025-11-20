# Security Configuration Guide

## ⚠️ IMPORTANT SECURITY NOTICE

This repository previously contained exposed API keys and credentials. If you're setting up this project, please follow this guide carefully to ensure proper security configuration.

## Quick Start Security Setup

### 1. Environment Variables Setup

**DO NOT hardcode any secrets in source code!**

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your actual values:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. Never commit `.env` to version control (it's already in `.gitignore`)

### 2. Required API Keys and Credentials

#### NOAA API Token
- **Get it at:** https://www.ncdc.noaa.gov/cdo-web/token
- **Steps:**
  1. Visit the URL above
  2. Enter your email
  3. Verify your email
  4. Copy the token to `.env`
  
```bash
NOAA_API_TOKEN=your_token_here
```

#### Django Secret Key
- **Generate it with:**
  ```bash
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  ```
- Add to `.env`:
  ```bash
  DJANGO_SECRET_KEY=your_generated_key_here
  ```

#### Email Configuration (Gmail)
- **Use Gmail App Password, NOT your account password**
- **Setup:**
  1. Enable 2-factor authentication on your Google account
  2. Go to: https://myaccount.google.com/apppasswords
  3. Generate an app password
  4. Add to `.env`:
  
```bash
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password_here
```

#### Mapbox Access Token
- **Get it at:** https://account.mapbox.com/access-tokens/
- **Important:** Configure URL restrictions in Mapbox dashboard
- Add to `.env`:
  ```bash
  MAPBOX_ACCESS_TOKEN=your_token_here
  ```

### 3. Verify Configuration

Run the setup script to verify your configuration:
```bash
python setup_api_tokens.py
```

### 4. Load Environment Variables

The application should automatically load variables from `.env`. If not, install python-dotenv:
```bash
pip install python-dotenv
```

And add to your Django settings or main application file:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Production Deployment

### Azure App Service

Set environment variables using Azure CLI:
```bash
az webapp config appsettings set \
  --name <your-app-name> \
  --resource-group <your-resource-group> \
  --settings \
    DJANGO_SECRET_KEY="<your-secret-key>" \
    NOAA_API_TOKEN="<your-token>" \
    EMAIL_HOST_PASSWORD="<your-password>"
```

Or use the Azure Portal:
1. Go to your App Service
2. Settings → Configuration
3. Add New Application Setting for each variable

### Environment-Specific Keys

**Use different keys for different environments:**
- Development: Use `.env` file locally
- Staging: Set in staging environment configuration
- Production: Set in production environment configuration
- **NEVER** use the same SECRET_KEY across environments

## Security Best Practices

### ✅ DO:
- Use environment variables for all secrets
- Use different credentials for dev/staging/production
- Rotate secrets regularly
- Use App Passwords for email services
- Configure URL restrictions for client-side tokens
- Review `.gitignore` before committing
- Use pre-commit hooks to catch secrets

### ❌ DON'T:
- Hardcode secrets in source code
- Commit `.env` files
- Share secrets in chat/email
- Reuse passwords across services
- Use production secrets in development
- Store secrets in plaintext files
- Commit `config/info.py` with real credentials

## Compromised Credentials

If you believe credentials have been exposed:

1. **Immediately revoke/rotate** the exposed credentials
2. Check git history for exposed secrets
3. Review access logs for unauthorized access
4. Enable 2-factor authentication where possible
5. Notify relevant stakeholders
6. Consider using tools like BFG Repo-Cleaner to purge history

## Secret Scanning Tools

Prevent accidental secret commits:

### Install pre-commit hooks:
```bash
pip install pre-commit detect-secrets
pre-commit install
```

### Scan repository for secrets:
```bash
# Using detect-secrets
pip install detect-secrets
detect-secrets scan > .secrets.baseline

# Using gitleaks
docker run -v $(pwd):/path zricethezav/gitleaks:latest detect --source="/path" -v

# Using truffleHog
docker run --rm -v $(pwd):/repo trufflesecurity/trufflehog:latest filesystem /repo
```

## Getting Help

- Review the detailed security audit: `SECURITY_AUDIT_REPORT.md`
- Check exposed secrets summary: `EXPOSED_SECRETS_SUMMARY.txt`
- For security issues, contact the security team
- For setup help, see main `README.md`

## References

- [Django Security Settings](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Application Security](https://owasp.org/www-project-top-ten/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)

---

**Last Updated:** November 20, 2024  
**Status:** Active
