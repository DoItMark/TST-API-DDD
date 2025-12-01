# Ringkasan Dokumentasi API

## File-file yang Telah Dibuat

### 📄 1. Dokumentasi API Sebelum JWT Authentication
**File:** `1_Dokumentasi_API_Sebelum_JWT.pdf`

**Isi:**
- Penjelasan struktur kode API sebelum implementasi JWT
- Detail tentang Aggregate Root (Listing) dan Domain Objects
- Penjelasan endpoints CRUD tanpa autentikasi
- Identifikasi kelemahan security (tidak ada autentikasi/otorisasi)
- Contoh request/response API

**Poin Utama:**
- API memiliki fungsionalitas lengkap tapi tidak aman
- Siapa saja bisa membuat, mengubah, atau menghapus listing
- Tidak ada verifikasi identitas atau kepemilikan
- Mudah untuk abuse dan sabotase

---

### 📄 2. Dokumentasi API Setelah JWT Authentication
**File:** `2_Dokumentasi_API_Setelah_JWT.pdf`

**Isi:**
- Perubahan struktur kode dengan implementasi JWT
- Dependencies baru (jwt, passlib/bcrypt)
- Model User dan Token
- Security functions (password hashing, token creation, authentication)
- Protected endpoints dengan ownership check
- Flow autentikasi lengkap
- HTTP status codes dan error handling

**Poin Utama:**
- Password di-hash dengan bcrypt
- JWT token expire setelah 30 menit
- Ownership check untuk semua operasi modifikasi
- User hanya bisa modify listing milik sendiri
- Clear separation antara public dan protected endpoints

---

### 📄 3. Panduan Instalasi dan Penggunaan
**File:** `3_Panduan_Instalasi_dan_Penggunaan.pdf`

**Isi:**
- **Instalasi:**
  - Setup project dan dependencies
  - Install FastAPI, Uvicorn, PyJWT, Passlib
  - Cara menjalankan server
  
- **Testing dengan cURL:**
  - Register user baru
  - Login dan dapatkan JWT token
  - Create/Update/Delete listing dengan authorization
  - Test error cases
  
- **Testing dengan Swagger UI:**
  - Cara menggunakan interactive documentation
  - Authorize dengan JWT token
  
- **Testing dengan Python Script:**
  - Contoh script otomatis untuk testing
  
- **Troubleshooting:**
  - Port already in use
  - Token expired
  - Import errors
  - Connection refused

---

## Perbandingan Sebelum vs Sesudah JWT

| Aspek | Sebelum JWT | Sesudah JWT |
|-------|-------------|-------------|
| **Autentikasi** | ❌ Tidak ada | ✅ JWT Token |
| **Password** | ❌ Tidak ada | ✅ Bcrypt hash |
| **Ownership** | ❌ Tidak ada check | ✅ Verifikasi owner |
| **Authorization** | ❌ Siapa saja bisa | ✅ Hanya owner |
| **Token Expiry** | ❌ N/A | ✅ 30 menit |
| **User Management** | ❌ Tidak ada | ✅ Register/Login |
| **Security** | ❌ Sangat lemah | ✅ Industry standard |

---

## Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Jalankan Server
```bash
python listing_api.py
```
atau
```bash
uvicorn listing_api:app --reload
```

### 3. Akses Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Register User
```bash
curl -X POST "http://localhost:8000/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"johndoe\", \"password\": \"password123\"}"
```

### 5. Login
```bash
curl -X POST "http://localhost:8000/login" ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"johndoe\", \"password\": \"password123\"}"
```

### 6. Create Listing (dengan token)
```bash
curl -X POST "http://localhost:8000/listings" ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"title\": \"Laptop Gaming\", ...}"
```

---

## Teknologi yang Digunakan

- **FastAPI**: Modern web framework untuk Python
- **Pydantic**: Data validation menggunakan Python type hints
- **PyJWT**: JSON Web Token implementation
- **Passlib**: Password hashing library
- **Bcrypt**: Secure password hashing algorithm
- **Uvicorn**: ASGI server untuk production

---

## Security Best Practices

✅ **Implemented:**
- Password hashing dengan bcrypt
- JWT untuk stateless authentication
- Token expiry (30 menit)
- Ownership verification
- Input validation dengan Pydantic

⚠️ **Untuk Production:**
- Ganti SECRET_KEY dengan secure random key
- Gunakan HTTPS only
- Implementasi rate limiting
- Gunakan database real (PostgreSQL/MySQL)
- Add logging dan monitoring
- Implementasi refresh tokens
- Add CORS configuration

---

## Domain-Driven Design (DDD)

API ini mengikuti prinsip DDD dengan:

- **Aggregate Root**: Listing (source of truth)
- **Entities**: Attribute
- **Value Objects**: Money, Condition, DelistReason, Filter
- **Domain Events**: ListingIndexedEvent
- **Read Model**: SearchIndexModel

---

## API Endpoints

### Public (Tidak perlu token):
- `POST /register` - Registrasi user baru
- `POST /login` - Login dan dapatkan token
- `GET /listings` - List semua listings
- `GET /listings/{id}` - Get detail listing
- `GET /search` - Search listings
- `GET /health` - Health check

### Protected (Perlu JWT token):
- `POST /listings` - Create listing baru
- `PATCH /listings/{id}/activate` - Activate listing
- `PATCH /listings/{id}/delist` - Delist listing
- `PATCH /listings/{id}/price` - Update harga
- `DELETE /listings/{id}` - Delete listing

---

## Kesimpulan

Implementasi JWT authentication telah mengubah API dari **tidak aman** menjadi **production-ready** dengan:

✅ User authentication dan authorization
✅ Password security dengan bcrypt
✅ Token-based session management
✅ Ownership verification
✅ Industry standard security practices

Dokumentasi lengkap tersedia dalam 3 PDF file yang mencakup penjelasan teknis, perbandingan sebelum/sesudah, dan panduan praktis penggunaan.

---

**Catatan:** Untuk penggunaan production, pastikan untuk mengikuti security best practices yang disebutkan di atas, terutama mengganti SECRET_KEY dan menggunakan database real.
