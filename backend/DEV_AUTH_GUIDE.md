# Development Authentication Guide

## Overview

For development, we use a simple header-based authentication system. In production, this will be replaced with JWT tokens.

## How to Use

### 1. Create Test User

Run the test user creation script:

```bash
cd backend
python scripts/create_test_user.py
```

This will create a test user and display the user ID.

### 2. Use in API Requests

Include the `X-DEV-USER-ID` header in all API requests:

```bash
curl -H "X-DEV-USER-ID: <user-id>" http://localhost:8000/api/v1/endpoint
```

### 4. In Frontend

When making API calls from the frontend, include the header:

```typescript
const response = await fetch('http://localhost:8000/api/v1/endpoint', {
  headers: {
    'X-DEV-USER-ID': '<user-id>',
    'Content-Type': 'application/json'
  }
});
```

## Test User Details

- **Email**: test@example.com
- **Password**: test123 (not used in dev auth, but stored for future)
- **Units**: kg
- **Timezone**: Asia/Kolkata

## Production

In production, this will be replaced with JWT authentication using the `Authorization` header.
