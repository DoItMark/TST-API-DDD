# Deployment Guide

This guide provides step-by-step instructions for deploying the TST-API-DDD (Item Management API) to various cloud platforms.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Security Best Practices](#security-best-practices)
- [Platform Deployment Guides](#platform-deployment-guides)
  - [Render (Recommended)](#render-recommended)
  - [Railway](#railway)
  - [Fly.io](#flyio)
  - [Heroku](#heroku)
- [Post-Deployment Verification](#post-deployment-verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

1. **Git repository** - Your code should be pushed to a Git repository (GitHub, GitLab, or Bitbucket)
2. **Python 3.11** - The application requires Python 3.11.0 as specified in `runtime.txt`
3. **Dependencies** - All dependencies are listed in `requirements.txt`
4. **Environment variables** - You'll need to configure the following:
   - `SECRET_KEY` - A secure secret key (minimum 32 characters)
   - `ALGORITHM` - JWT algorithm (default: HS256)
   - `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 30)

---

## Security Best Practices

### ⚠️ CRITICAL: SECRET_KEY Configuration

**NEVER** use the default SECRET_KEY in production! Follow these steps:

1. **Generate a secure SECRET_KEY:**
   ```bash
   # Using Python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Or using OpenSSL
   openssl rand -base64 32
   ```

2. **Keep it secret:**
   - Never commit your SECRET_KEY to Git
   - Use environment variables on your deployment platform
   - Store it securely in your deployment platform's secrets manager

3. **Use strong, unique keys:**
   - Minimum 32 characters
   - Use cryptographically secure random generation
   - Use a different key for each environment (development, staging, production)

---

## Platform Deployment Guides

### Render (Recommended)

Render offers a generous free tier and is beginner-friendly.

#### Step 1: Create a Render Account
1. Go to [render.com](https://render.com)
2. Sign up using your GitHub account (recommended for easy repository access)

#### Step 2: Create a New Web Service
1. Click **"New +"** button in the Render dashboard
2. Select **"Web Service"**
3. Connect your GitHub repository
4. Select the repository containing your TST-API-DDD project

#### Step 3: Configure Your Service
Fill in the following settings:

- **Name:** `tst-api-ddd` (or your preferred name)
- **Region:** Choose the closest to your users
- **Branch:** `main` (or your deployment branch)
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn listing_api:app --host 0.0.0.0 --port $PORT`

#### Step 4: Configure Environment Variables
In the **Environment Variables** section, add:

1. Click **"Add Environment Variable"**
2. Add each variable:
   ```
   SECRET_KEY = [Your generated secret key - 32+ characters]
   ALGORITHM = HS256
   ACCESS_TOKEN_EXPIRE_MINUTES = 30
   ```

#### Step 5: Deploy
1. Click **"Create Web Service"**
2. Render will automatically build and deploy your application
3. Wait for the deployment to complete (usually 2-5 minutes)
4. Your API will be available at: `https://your-service-name.onrender.com`

#### Step 6: Configure Auto-Deploy (Optional)
- Render automatically deploys on every push to your main branch
- You can disable this in the service settings if needed

---

### Railway

Railway provides a simple deployment experience with a generous free tier.

#### Step 1: Create a Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub

#### Step 2: Create a New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your TST-API-DDD repository

#### Step 3: Configure the Service
Railway will auto-detect your Python application.

1. Go to **Variables** tab
2. Add environment variables:
   ```
   SECRET_KEY = [Your generated secret key]
   ALGORITHM = HS256
   ACCESS_TOKEN_EXPIRE_MINUTES = 30
   ```

#### Step 4: Configure the Start Command
1. Go to **Settings** tab
2. Under **Deploy**, set the start command:
   ```
   uvicorn listing_api:app --host 0.0.0.0 --port $PORT
   ```

#### Step 5: Deploy
1. Railway will automatically deploy your application
2. Once deployed, click **"Generate Domain"** to get a public URL
3. Your API will be available at: `https://your-project.up.railway.app`

---

### Fly.io

Fly.io offers global deployment with edge computing capabilities.

#### Step 1: Install Fly CLI
```bash
# On macOS
brew install flyctl

# On Linux
curl -L https://fly.io/install.sh | sh

# On Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
```

#### Step 2: Login to Fly.io
```bash
flyctl auth login
```

#### Step 3: Launch Your Application
From your project directory:
```bash
flyctl launch
```

The `fly.toml` file in the repository contains the configuration. Fly will:
- Detect your application
- Ask for an app name (or use the default)
- Select a region

#### Step 4: Set Environment Variables
```bash
flyctl secrets set SECRET_KEY="your-generated-secret-key-here"
flyctl secrets set ALGORITHM="HS256"
flyctl secrets set ACCESS_TOKEN_EXPIRE_MINUTES="30"
```

#### Step 5: Deploy
```bash
flyctl deploy
```

Your API will be available at: `https://your-app-name.fly.dev`

#### Step 6: Monitor Your Application
```bash
# View logs
flyctl logs

# Check status
flyctl status
```

---

### Heroku

**Note:** Heroku eliminated its free tier in November 2022. You'll need a paid plan.

#### Step 1: Install Heroku CLI
```bash
# On macOS
brew install heroku/brew/heroku

# On Windows
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# On Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

#### Step 2: Login to Heroku
```bash
heroku login
```

#### Step 3: Create a Heroku App
```bash
heroku create your-app-name
```

#### Step 4: Set Environment Variables
```bash
heroku config:set SECRET_KEY="your-generated-secret-key-here"
heroku config:set ALGORITHM="HS256"
heroku config:set ACCESS_TOKEN_EXPIRE_MINUTES="30"
```

#### Step 5: Deploy
```bash
git push heroku main
```

If you're on a different branch:
```bash
git push heroku your-branch:main
```

#### Step 6: Open Your Application
```bash
heroku open
```

Your API will be available at: `https://your-app-name.herokuapp.com`

---

## Post-Deployment Verification

After deployment, verify your API is working correctly:

### 1. Check Health Endpoint
```bash
curl https://your-app-url.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "listings_count": 0,
  "search_index_count": 0
}
```

### 2. Test User Registration
```bash
curl -X POST https://your-app-url.com/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword123"
  }'
```

### 3. Test User Login
```bash
curl -X POST https://your-app-url.com/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword123"
  }'
```

You should receive an access token in the response.

### 4. Access API Documentation
Navigate to:
- **Swagger UI:** `https://your-app-url.com/docs`
- **ReDoc:** `https://your-app-url.com/redoc`

These interfaces provide interactive API documentation.

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Fails to Start

**Symptom:** Deployment succeeds but app crashes on startup

**Solutions:**
- Check the logs for specific error messages
- Verify all dependencies are in `requirements.txt`
- Ensure Python version matches `runtime.txt` (3.11.0)
- Check that environment variables are properly set

**Platform-specific log commands:**
```bash
# Render: Check logs in the dashboard
# Railway: Click "View Logs" in the dashboard
# Fly.io
flyctl logs

# Heroku
heroku logs --tail
```

#### 2. Secret Key Errors

**Symptom:** JWT validation errors or authentication failures

**Solutions:**
- Ensure `SECRET_KEY` is set in environment variables
- Verify the key is at least 32 characters long
- Make sure there are no extra spaces or quotes in the value

**Verify environment variables:**
```bash
# Fly.io
flyctl secrets list

# Heroku
heroku config

# Render/Railway: Check in the dashboard
```

#### 3. Port Binding Issues

**Symptom:** App crashes with "Address already in use" or similar error

**Solutions:**
- Ensure your start command uses `$PORT` environment variable
- Correct start command: `uvicorn listing_api:app --host 0.0.0.0 --port $PORT`
- The platform automatically sets the `$PORT` variable

#### 4. Database/Storage Issues

**Note:** This application uses in-memory storage. All data is lost when the application restarts.

**For production use, you should:**
- Implement a persistent database (PostgreSQL, MongoDB, etc.)
- Add database connection configuration to environment variables
- Update the code to use database instead of in-memory dictionaries

#### 5. CORS Errors (if accessing from a frontend)

**Symptom:** Browser shows CORS policy errors

**Solution:** Add CORS middleware to `listing_api.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 6. Build Failures

**Symptom:** Deployment fails during build

**Common causes:**
- Missing dependencies in `requirements.txt`
- Python version mismatch
- Syntax errors in code

**Solutions:**
- Test build locally: `pip install -r requirements.txt`
- Check build logs for specific error messages
- Verify Python version: `python --version`

---

## Additional Resources

### Platform Documentation
- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Fly.io Docs](https://fly.io/docs)
- [Heroku Docs](https://devcenter.heroku.com)

### FastAPI Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Uvicorn Documentation](https://www.uvicorn.org)

### Security Resources
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## Notes for Development

### Local Development
To run locally without deployment:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn listing_api:app --reload
   ```

3. Access the API at: `http://localhost:8000`

### Environment Variables for Local Development
Create a `.env` file (already in `.gitignore`) based on `.env.example`:
```bash
cp .env.example .env
```

Then edit `.env` with your local values. The application works with default values if environment variables are not set.

---

## Support

For issues specific to:
- **The API code:** Create an issue in the GitHub repository
- **Platform deployment:** Contact the respective platform's support
- **General FastAPI questions:** Check [FastAPI Discussion Forum](https://github.com/tiangolo/fastapi/discussions)

---

**Last Updated:** 2026-01-03
