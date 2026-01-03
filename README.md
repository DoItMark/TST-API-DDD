# TST-API-DDD: Item Management API

RESTful API untuk manajemen listing item dengan Domain-Driven Design (DDD) principles, dilengkapi JWT authentication dan comprehensive testing.

🚀 **Live API:** https://api-tst.onrender.com

[![CI/CD](https://github.com/DoItMark/TST-API-DDD/actions/workflows/ci.yml/badge.svg)](https://github.com/DoItMark/TST-API-DDD/actions)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)](htmlcov/index.html)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Authentication](#-authentication)
- [API Endpoints](#-api-endpoints)
- [Usage Examples](#-usage-examples)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Tech Stack](#-tech-stack)

---

## ✨ Features

- ✅ **Domain-Driven Design** - Aggregate Root, Value Objects, Entities, Domain Events
- ✅ **JWT Authentication** - Secure token-based authentication
- ✅ **Password Hashing** - Bcrypt untuk keamanan password
- ✅ **Ownership Validation** - Authorization berbasis seller
- ✅ **Search Functionality** - Full-text search dengan relevance scoring
- ✅ **State Management** - Listing states (ACTIVE/DELISTED)
- ✅ **Auto-generated Docs** - Interactive Swagger UI
- ✅ **94% Test Coverage** - 44 comprehensive tests
- ✅ **CI/CD Pipeline** - GitHub Actions automation
- ✅ **Production Ready** - Deployed on Render.com

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (recommended: 3.13)
- pip package manager
- Virtual environment (recommended)

### Installation

```bash
# Clone repository
git clone https://github.com/DoItMark/TST-API-DDD.git
cd TST-API-DDD

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Locally

```bash
# Start server
uvicorn listing_api:app --reload

# Server akan berjalan di:
# http://127.0.0.1:8000
```

### Access API Documentation

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

---

## 📖 API Documentation

### Base URL

**Production:** `https://api-tst.onrender.com`  
**Local:** `http://127.0.0.1:8000`

### Health Check

```bash
curl https://api-tst.onrender.com/health
```

Response:
```json
{
  "status": "healthy"
}
```

---

## 🔐 Authentication

API menggunakan **JWT (JSON Web Token)** untuk authentication.

### 1. Register User

**Endpoint:** `POST /register`

```bash
curl -X POST https://api-tst.onrender.com/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password123",
    "full_name": "John Doe"
  }'
```

**Response:**
```json
{
  "username": "john_doe",
  "full_name": "John Doe",
  "message": "User registered successfully"
}
```

### 2. Login

**Endpoint:** `POST /login`

```bash
curl -X POST https://api-tst.onrender.com/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=secure_password123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Use Token for Protected Endpoints

```bash
curl -X GET https://api-tst.onrender.com/listings \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Token expiry:** 30 minutes

---

## 📍 API Endpoints

### Public Endpoints (No Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/register` | Register new user |
| `POST` | `/login` | Login user |
| `GET` | `/listings` | Get all listings |
| `GET` | `/listings/{id}` | Get listing by ID |
| `GET` | `/search` | Search listings |

### Protected Endpoints (Require JWT)

| Method | Endpoint | Description | Authorization |
|--------|----------|-------------|---------------|
| `POST` | `/listings` | Create listing | Authenticated user |
| `PUT` | `/listings/{id}/price` | Update price | Owner only |
| `PUT` | `/listings/{id}/activate` | Activate listing | Owner only |
| `PUT` | `/listings/{id}/delist` | Delist listing | Owner only |
| `DELETE` | `/listings/{id}` | Delete listing | Owner only |

---

## 💡 Usage Examples

### 1. Register & Login Flow

```bash
# Step 1: Register
curl -X POST https://api-tst.onrender.com/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seller1",
    "password": "mypassword123",
    "full_name": "First Seller"
  }'

# Step 2: Login to get token
TOKEN=$(curl -X POST https://api-tst.onrender.com/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=seller1&password=mypassword123" \
  | jq -r '.access_token')

echo $TOKEN
```

### 2. Create Listing

```bash
curl -X POST https://api-tst.onrender.com/listings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "item_name": "iPhone 15 Pro",
    "description": "Brand new iPhone 15 Pro, 256GB, Blue Titanium",
    "price": {
      "amount": 15000000,
      "currency": "IDR"
    },
    "condition": {
      "state": "NEW",
      "notes": "Sealed in original box"
    },
    "attributes": [
      {
        "key": "Storage",
        "value": "256GB"
      },
      {
        "key": "Color",
        "value": "Blue Titanium"
      }
    ]
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "item_name": "iPhone 15 Pro",
  "description": "Brand new iPhone 15 Pro, 256GB, Blue Titanium",
  "price": {
    "amount": 15000000.0,
    "currency": "IDR"
  },
  "condition": {
    "state": "NEW",
    "notes": "Sealed in original box"
  },
  "seller_id": "seller1",
  "item_state": "ACTIVE",
  "attributes": [
    {
      "id": "attr-123",
      "key": "Storage",
      "value": "256GB"
    },
    {
      "id": "attr-456",
      "key": "Color",
      "value": "Blue Titanium"
    }
  ],
  "created_at": "2026-01-04T10:30:00",
  "updated_at": "2026-01-04T10:30:00"
}
```

### 3. Get All Listings

```bash
# Public access - no authentication needed
curl https://api-tst.onrender.com/listings
```

**Query Parameters:**
- `seller_id` - Filter by seller
- `skip` - Pagination offset (default: 0)
- `limit` - Items per page (default: 100)

**Example with filters:**
```bash
curl "https://api-tst.onrender.com/listings?seller_id=seller1&limit=10"
```

### 4. Get Listing by ID

```bash
curl https://api-tst.onrender.com/listings/550e8400-e29b-41d4-a716-446655440000
```

### 5. Search Listings

```bash
curl "https://api-tst.onrender.com/search?query=iPhone&min_relevance=0.3"
```

**Query Parameters:**
- `query` - Search keywords
- `min_relevance` - Minimum relevance score (0.0-1.0, default: 0.1)
- `skip` - Pagination offset
- `limit` - Items per page

**Response:**
```json
[
  {
    "listing_id": "550e8400-e29b-41d4-a716-446655440000",
    "item_name": "iPhone 15 Pro",
    "description": "Brand new iPhone 15 Pro...",
    "price": {"amount": 15000000.0, "currency": "IDR"},
    "seller_id": "seller1",
    "relevance_score": 0.95
  }
]
```

### 6. Update Listing Price (Owner Only)

```bash
curl -X PUT https://api-tst.onrender.com/listings/550e8400-e29b-41d4-a716-446655440000/price \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 14500000,
    "currency": "IDR"
  }'
```

### 7. Activate Listing (Owner Only)

```bash
curl -X PUT https://api-tst.onrender.com/listings/550e8400-e29b-41d4-a716-446655440000/activate \
  -H "Authorization: Bearer $TOKEN"
```

### 8. Delist Listing (Owner Only)

```bash
curl -X PUT https://api-tst.onrender.com/listings/550e8400-e29b-41d4-a716-446655440000/delist \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "SOLD",
    "notes": "Sold to local buyer"
  }'
```

**Delist Reasons:**
- `SOLD` - Item has been sold
- `OUT_OF_STOCK` - No longer available
- `POLICY_VIOLATION` - Violates platform policy
- `OTHER` - Other reasons

### 9. Delete Listing (Owner Only)

```bash
curl -X DELETE https://api-tst.onrender.com/listings/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🧪 Testing

### Run Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest -v

# Run with coverage
pytest --cov=listing_api --cov-report=term-missing -v

# Run with HTML coverage report
pytest --cov=listing_api --cov-report=html -v
# Open htmlcov/index.html in browser
```

### Test Coverage

```
Name             Stmts   Miss  Cover   Missing
----------------------------------------------
listing_api.py     264     16    94%   
----------------------------------------------
```

**Test Suite:**
- 44 total tests
- 8 Authentication tests
- 11 Listing Operations tests
- 8 Security tests
- 5 Search Functionality tests
- 1 Health Check test
- 11 Edge Cases tests

---

## 🌐 Deployment

### Production Deployment (Render)

API ini di-deploy di **Render.com** dengan konfigurasi:

- **URL:** https://api-tst.onrender.com
- **Runtime:** Python 3.13
- **Auto-deploy:** Enabled (dari branch `main`)
- **Health Check:** `/health` endpoint
- **HTTPS:** Enabled (automatic SSL)

### Manual Deployment

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn listing_api:app --host 0.0.0.0 --port $PORT
```

### CI/CD Pipeline

GitHub Actions workflow otomatis:
1. ✅ Run tests pada Python 3.11, 3.12, 3.13
2. ✅ Check coverage ≥ 80%
3. ✅ Generate coverage reports
4. ✅ Upload artifacts

**View CI/CD:** [GitHub Actions](https://github.com/DoItMark/TST-API-DDD/actions)

---

## 🛠 Tech Stack

### Backend
- **FastAPI** 0.115.5 - Modern Python web framework
- **Uvicorn** 0.34.0 - ASGI server
- **Pydantic** 2.10.5 - Data validation
- **PyJWT** 2.10.1 - JWT implementation
- **Passlib** 1.7.4 - Password hashing
- **Bcrypt** 4.0.1 - Encryption

### Testing
- **Pytest** 8.3.4 - Testing framework
- **pytest-cov** 6.0.0 - Coverage plugin
- **pytest-asyncio** 0.24.0 - Async testing
- **httpx** 0.28.1 - HTTP client for testing

### CI/CD
- **GitHub Actions** - Automation
- **Render** - Deployment platform

---

## 📂 Project Structure

```
TST-API-DDD/
├── listing_api.py              # Main API file
├── test_listing_api.py         # Test suite
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Dev dependencies
├── pytest.ini                  # Pytest configuration
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline
├── docs/                       # Documentation
│   ├── docs_before_jwt.md
│   ├── docs_after_jwt.md
│   └── installation_usage_guide.md
└── README.md                   # This file
```

---

## 🔒 Security

- ✅ JWT token authentication
- ✅ Password hashing with bcrypt
- ✅ Ownership-based authorization
- ✅ Input validation with Pydantic
- ✅ HTTPS enabled in production

**Security Considerations:**
- Tokens expire after 30 minutes
- Passwords hashed with bcrypt (cost factor 12)
- Protected endpoints require valid JWT
- Owner validation for sensitive operations

---

## 📊 Performance

### Response Times (Production)

| Endpoint | Avg Response Time |
|----------|-------------------|
| `/health` | ~50ms |
| `/listings` | ~100-200ms |
| `/search` | ~150-300ms |
| `/login` | ~200-300ms (bcrypt hashing) |

**Note:** First request after cold start may take ~30 seconds (Render free tier limitation)

---

## 🤝 Contributing

Proyek ini adalah tugas kuliah. Kontribusi terbatas untuk tujuan pembelajaran.

---

## 📄 License

MIT License - Educational purposes

---

## 👨‍💻 Author

**Mark (18223130)**  
Teknologi Sistem Terintegrasi (II3160)  
Institut Teknologi Bandung

---

## 📞 Support

Untuk pertanyaan atau issues:
- GitHub Issues: [Create an issue](https://github.com/DoItMark/TST-API-DDD/issues)
- API Documentation: https://api-tst.onrender.com/docs

---

## 🙏 Acknowledgments

- **GitHub Copilot** - AI pair programming assistance
- **FastAPI** - Excellent framework documentation
- **Render** - Free hosting platform
- **Domain-Driven Design** - Eric Evans' principles

---

**Last Updated:** January 4, 2026  
**API Version:** 1.0.0
Project for college - Integrated Technology and System
