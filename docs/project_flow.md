# Project Flow

This document outlines the high-level request flow through the service.

## Request Path Overview

```
Client
  |
  v
FastAPI Router (src/api/routes)
  |
  v
Pydantic Schemas (src/schemas)
  |
  v
Repository Layer (src/repositories)
  |
  v
Async DB Session (src/database/db_helpers.py)
  |
  v
PostgreSQL (users table)
```

## User Registration Flow

```
POST /users/register-user
  -> validate payload (Pydantic)
  -> check password confirmation
  -> query for existing user by email/mobile
  -> hash password
  -> insert user record
  -> return UserSignUpResponse
```

## User Lookup Flow

```
GET /users/get-users-details?query=<email|mobile>
  -> build SELECT based on query type
  -> fetch records
  -> return list of UserDetailesResponse
```

## Welcome Route

```
GET /
  -> return greeting payload
```

