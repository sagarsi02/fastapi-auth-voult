# 🔐 FastAPI JWT Authentication System (Step-by-Step Guide)

This document describes a **secure, production-ready authentication system** using **FastAPI, JWT, and PostgreSQL**.
We will build this system **step by step**, following best practices used in real-world backend systems.

---

## 🧰 Tech Stack

* **Backend Framework:** FastAPI
* **Authentication:** JWT (Access Token + Refresh Token)
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy (Async)
* **Password Hashing:** bcrypt / passlib
* **Migrations:** Alembic
* **Token Transport:** Authorization Header (Bearer)

---

## 🎯 Goals of the Authentication System

* Secure **Signup / Login / Logout** flow
* JWT-based authentication
* Session-like behavior using database
* If user is **already logged in**, no need to login again
* Token expiration & refresh mechanism
* Support multiple devices & logout-all feature
* Clean, scalable project structure

---

## 🏗️ High-Level Architecture

```
Client (Web / Mobile)
        |
        |  Access Token (JWT)
        |
FastAPI (Auth Middleware)
        |
PostgreSQL (Users + Sessions)
```

---

## 🗄️ Database Design

### 👤 Users Table

```sql
users
-----
id (UUID, PK)
email (unique, indexed)
username (unique)
password_hash
is_active (boolean)
is_verified (boolean)
created_at
updated_at
```

---

### 🔑 User Sessions Table (Session-Based Login)

```sql
user_sessions
-------------
id (UUID, PK)
user_id (FK → users.id)
refresh_token (unique)
user_agent
ip_address
is_active (boolean)
expires_at
created_at
```

📌 This table enables **session-based behavior** even with JWT.

---

## 🔐 JWT Token Strategy (Best Practice)

### 🔹 Access Token

* Short-lived (10–15 minutes)
* Used for accessing protected APIs
* Sent in `Authorization: Bearer <token>` header

### 🔹 Refresh Token

* Long-lived (7–30 days)
* Stored securely in DB
* Used to generate new access tokens

---

## 🛡️ Security Best Practices

* ✅ Password hashing using **bcrypt**
* ✅ Never store plain-text passwords
* ✅ Short-lived access tokens
* ✅ Refresh tokens stored in DB
* ✅ Logout revokes refresh token
* ✅ Rate limit login endpoint
* ✅ HTTPS only (production)
* ✅ Strong JWT secret
* ✅ Token expiration validation
* ✅ Email verification (optional)

---

## 📁 Project Structure

```
app/
├── main.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── jwt.py
├── db/
│   ├── base.py
│   ├── session.py
│   └── models.py
├── auth/
│   ├── router.py
│   ├── service.py
│   ├── schemas.py
│   └── dependencies.py
├── users/
│   ├── router.py
│   └── service.py
└── migrations/
```

---

## 🚀 Step-by-Step Feature Development

---

## 1️⃣ User Signup

### Endpoint

```
POST /auth/signup
```

### Flow

1. Validate email & password strength
2. Hash password using bcrypt
3. Save user in database
4. Set `is_active = true`
5. Return success response

### Password Rules

* Minimum 8 characters
* At least 1 uppercase letter
* At least 1 number
* At least 1 special character

---

## 2️⃣ User Login

### Endpoint

```
POST /auth/login
```

### Flow

1. Validate user credentials
2. Verify password hash
3. Check if active session exists
4. If session exists:

   * Return existing tokens
5. Else:

   * Create new session
   * Generate access & refresh tokens
   * Store refresh token in DB

### Response

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

---

## 3️⃣ Already Logged-In Session Handling

### Logic

* If user already has an **active session** in DB
* Same user-agent / IP (optional)
* Do not create a new session
* Reuse existing refresh token

🎯 Prevents unnecessary multiple logins

---

## 4️⃣ Access Protected APIs

### Mechanism

* Use FastAPI dependency:

```python
Depends(get_current_user)
```

### Flow

1. Extract JWT from header
2. Verify signature
3. Check expiry
4. Extract `user_id`
5. Fetch user from DB
6. Allow request

---

## 5️⃣ Refresh Token

### Endpoint

```
POST /auth/refresh
```

### Flow

1. Validate refresh token
2. Verify active session in DB
3. Generate new access token
4. Return new token

---

## 6️⃣ Logout

### Endpoint

```
POST /auth/logout
```

### Flow

1. Identify session via refresh token
2. Mark session as inactive
3. Invalidate refresh token
4. User logged out successfully

---

## 7️⃣ Logout from All Devices

### Endpoint

```
POST /auth/logout-all
```

### Flow

* Deactivate all sessions for user
* Forces re-login on all devices

---

## ⚙️ Environment Variables

```env
JWT_SECRET_KEY=super-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
```

---

## 🌟 Optional Advanced Features

* 🔥 Role-based access (Admin/User)
* 🔥 Account lock after failed attempts
* 🔥 Multi-device session tracking
* 🔥 Two-factor authentication (2FA)
* 🔥 Login activity audit logs

---

## ✅ Final Summary

✔ Secure JWT authentication
✔ Session-based login behavior
✔ No repeated login if already active
✔ Scalable FastAPI architecture
✔ Production-ready best practices

---

📌 **Next Steps**

We will now build this system **step by step**:

1. Project setup & config
2. Database models
3. JWT utility
4. Signup API
5. Login & session logic
6. Protected routes
7. Refresh & logout

👉 Ready to start with **Step 1: Project Setup** 🚀
