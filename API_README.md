# Item Management API - DDD Implementation

This is a Python FastAPI implementation based on the Listing Aggregate from the ItemManagement_ClassDiagram.

## Features

- **Domain-Driven Design**: Implements Aggregate Root pattern with Listing as the source of truth
- **JWT Authentication**: Secure API endpoints with JSON Web Tokens
- **Password Hashing**: Bcrypt-based password security
- **Authorization**: Owner-based access control for listings
- **Value Objects**: Money, Condition, DelistReason, Filter
- **Entities**: Attribute
- **Domain Events**: ListingIndexedEvent
- **Read Model**: SearchIndexModel for optimized queries
- **RESTful API**: Complete CRUD operations for listings

## Installation

```bash
pip install -r requirements.txt
```

## Running the API

```bash
python listing_api.py
```

Or using uvicorn directly:
```bash
uvicorn listing_api:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

#### Register User
```
POST /register
```

#### Login
```
POST /login
```

### Listings (Protected - Requires JWT Token)

### Create Listing
```
POST /listings
```

### Get Listing
```
GET /listings/{listing_id}
```

### List Listings
```
GET /listings?seller_id={uuid}&item_state={Active|Sold|Delisted}
```

### Activate Listing
```
PATCH /listings/{listing_id}/activate
```

### Delist Listing
```
PATCH /listings/{listing_id}/delist
```

### Update Price
```
PATCH /listings/{listing_id}/price
```

### Delete Listing
```
DELETE /listings/{listing_id}
```

### Search Listings
```
GET /search?query={text}&min_relevance={float}
```

### Health Check
```
GET /health
```

## Example Usage

### Register a User
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepassword123"
  }'
```

### Login and Get Token
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Create a Listing (with JWT Token)
```bash
curl -X POST "http://localhost:8000/listings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Vintage Camera",
    "price": {
      "amount": 299.99,
      "currency": "USD"
    },
    "condition": {
      "score": 8,
      "detailed_description": "Good condition with minor wear",
      "known_defects": ["Small scratch on lens cap"]
    },
    "attributes": [
      {
        "name": "Brand",
        "value": "Canon"
      },
      {
        "name": "Year",
        "value": "1985"
      }
    ]
  }'
```

### Update Price (with JWT Token)
```bash
curl -X PATCH "http://localhost:8000/listings/{listing_id}/price" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "new_price": {
      "amount": 249.99,
      "currency": "USD"
    }
  }'
```

### Delist a Listing (with JWT Token)
```bash
curl -X PATCH "http://localhost:8000/listings/{listing_id}/delist" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "reason": {
      "reason_type": "SellerRequest",
      "detail": "Item no longer available"
    }
  }'
```

## Domain Model

The API implements the following domain concepts:

- **Listing (Aggregate Root)**: Main entity managing item listings
- **Attribute (Entity)**: Custom attributes for items
- **Money (Value Object)**: Immutable price representation
- **Condition (Value Object)**: Item condition details
- **DelistReason (Value Object)**: Reason for delisting
- **SearchIndexModel (Read Model)**: Optimized for search queries
- **ListingIndexedEvent (Domain Event)**: Published when listing is indexed

## Notes

- Currently uses in-memory storage (replace with a database for production)
- **Change SECRET_KEY in production!** Use a secure random key (min 32 characters)
- JWT tokens expire after 30 minutes (configurable)
- Protected endpoints require Bearer token in Authorization header
- Users can only modify their own listings (ownership check)
- Events are generated but not persisted (implement event store for production)
- Search functionality is basic (integrate with Elasticsearch for production)
